"""Linux fork: the scene render size of an Uncharted game (a BBPATCH2 file for bb-probe --patches).

The collection's engine keeps its video settings in one default setup whose size fields (scene, UI,
viewport) are 1920x1080, with the 16:9 aspect ratio beside them. The port's own output size
setting (bbport.ini output_res) does not reach a game here: the games run in the port's velocity
mode, which keeps the guest at the game's own size and scales only the finished picture. A game
therefore renders at 1080p whatever the Steam Deck mode or the output size says, until these
fields are patched. The sites are found by their instruction bytes, the same in all three games.

    python3 render_size.py <prepared eboot.elf> <out.bin> <WxH> [--merge <other BBPATCH2 file>]

decide() chooses the size from the environment (run.py):
    BB_RENDER_SIZE=WxH   an explicit size, at most 1920x1080 (sizes above 1080p are another feature)
    BB_RENDER_720P=1     1280x720, the Steam Deck mode's size (the same switch as the fork upstream's)
"""
import re
import struct
import sys

NATIVE = (1920, 1080)
DECK = (1280, 720)
LIMITS = (320, 180, 1920, 1080)  # smallest and largest width, height
# movl $1920, 0x8(%rdi|%rax); movl $1080, 0xc(%rdi|%rax): the first two size fields of a setup.
SITE = re.compile(rb'\xc7[\x40\x47]\x08\x80\x07\x00\x00\xc7[\x40\x47]\x0c\x38\x04\x00\x00')
WINDOW = 0x90          # the fields of one setup follow within this many bytes
ASPECT_FIELDS = (0x20, 0x2c)
ASPECT_16_9 = struct.pack('<f', 16 / 9)
# movl $1920, d(%rsp); movl $1088, d+4(%rsp): the movie decoder's maximum frame size. The movie
# shader maps the picture to that size, so it follows the scene (the decoder scales frames down).
DECODER = re.compile(rb'\xc7\x44\x24(.)\x80\x07\x00\x00\xc7\x44\x24(.)\x40\x04\x00\x00', re.S)


def parse_size(text):
    """(width, height) for 'WxH' when it is usable as a scene size, else None."""
    try:
        w, h = (int(v) for v in str(text).lower().split('x'))
    except ValueError:
        return None
    # The engine has half and eighth resolution buffers: width a multiple of 8, height of 4.
    if w % 8 or h % 4 or not (LIMITS[0] <= w <= LIMITS[2] and LIMITS[1] <= h <= LIMITS[3]):
        return None
    return (w, h)


def decide(env):
    """The scene size to patch in, or None for the game's own 1920x1080."""
    size = parse_size(env.get('BB_RENDER_SIZE', ''))
    if size is None and env.get('BB_RENDER_720P') == '1':
        size = DECK
    return None if size in (None, NATIVE) else size


def image_base(elf):
    """File offset minus image offset of the first program header (the image maps vaddr 0 at 0)."""
    phoff = struct.unpack_from('<Q', elf, 0x20)[0]
    _, _, offset, vaddr, *_ = struct.unpack_from('<IIQQQQQQ', elf, phoff)
    return offset - vaddr


def find_sites(elf):
    return [m.start() for m in SITE.finditer(elf)]


def writes(elf, size):
    """[(image offset, bytes)] that make the game's setup render at `size`."""
    width, height = size
    sites = find_sites(elf)
    if not sites:
        raise ValueError('no 1920x1080 video setup found in this executable')
    base = image_base(elf)
    new = {1920: width, 1080: height, 1920 // 8: width // 8, 1080 // 4: height // 4}
    out = []
    for index, site in enumerate(sites):
        end = min(site + WINDOW, sites[index + 1] - 9 if index + 1 < len(sites) else len(elf))
        for at in range(site, end):
            # movl $imm32, disp8(%reg): the immediate starts 3 bytes after the opcode
            if elf[at - 3] != 0xc7 or elf[at - 2] not in (0x40, 0x47):
                continue
            field, value = elf[at - 1], struct.unpack_from('<I', elf, at)[0]
            if value in (1920 // 8, 1080 // 4) and field not in (0x40, 0x44):
                continue   # 240x270 only in the setup's eighth-resolution fields
            if value in new and (value in (1920, 1080) or field in (0x40, 0x44)):
                out.append((at - base, struct.pack('<I', new[value])))
            elif field in ASPECT_FIELDS and elf[at:at + 4] == ASPECT_16_9 and width * 9 != height * 16:
                out.append((at - base, struct.pack('<f', width / height)))
    decoders = [m for m in DECODER.finditer(elf) if m.group(2)[0] == m.group(1)[0] + 4]
    if len(decoders) == 1:
        at = decoders[0].start()
        out.append((at + 4 - base, struct.pack('<I', width)))
        out.append((at + 12 - base, struct.pack('<I', height)))
    return out


def blob_of(found, patch_base=0x400000):
    blob = b'BBPATCH2' + struct.pack('<QQ', patch_base, len(found))
    for offset, data in found:
        blob += struct.pack('<QQ', offset, len(data)) + data
    return blob


def patch_bytes(elf, size):
    return blob_of(writes(elf, size))


def entries(blob):
    magic, base, count = struct.unpack_from('<8sQQ', blob)
    if magic != b'BBPATCH2':
        raise ValueError('not a BBPATCH2 file')
    at, found = 24, []
    for _ in range(count):
        offset, size = struct.unpack_from('<QQ', blob, at)
        found.append((offset, blob[at + 16:at + 16 + size]))
        at += 16 + size
    return base, found


def merge(other, ours):
    """One BBPATCH2 blob with the entries of both (ours last: they win where bytes overlap)."""
    base, found = entries(other)
    return blob_of(found + entries(ours)[1], base)


def main(argv):
    merge_with = None
    if '--merge' in argv:
        at = argv.index('--merge')
        merge_with = argv[at + 1]
        argv = argv[:at] + argv[at + 2:]
    elf_path, out_path, text = argv[1:4]
    size = parse_size(text)
    if size is None:
        raise ValueError(f'unusable render size {text!r}')
    with open(elf_path, 'rb') as f:
        blob = patch_bytes(f.read(), size)
    if merge_with:
        with open(merge_with, 'rb') as f:
            blob = merge(f.read(), blob)
    with open(out_path, 'wb') as f:
        f.write(blob)
    print(f'Render size: scene {size[0]}x{size[1]} ({entries(blob)[1].__len__()} values patched)')


if __name__ == '__main__':
    try:
        main(sys.argv)
    except (OSError, ValueError, struct.error, IndexError) as error:
        print(f'Render size: {error}')
        sys.exit(1)
