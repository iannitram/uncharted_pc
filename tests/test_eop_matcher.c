/* The frame-pacing patch in probe.c: patch_eop_tick_wait finds the game's "EOP tick" assertion
 * through its message and turns the failed check into pause + jump back to the check. These
 * tests feed it small synthetic x86-64 images (no game bytes) with the instruction shapes the
 * matcher accepts, and a few that it must leave alone. probe.c is included whole, with its
 * main renamed, so the static function and the image global are reachable. */
#define _GNU_SOURCE
/* probe's main falls off its end (implicitly 0); renamed, that is a -Wreturn-type error */
#pragma GCC diagnostic ignored "-Wreturn-type"
#define main bb_probe_main
#include "../src/probe.c"
#undef main
#include <assert.h>

static const char message[]="GetRenderFrameParams(frameToFreeInstancesFor)->m_gfxEopTick";
#define SIZE 0x800u
#define MESSAGE_AT 0x600u

static unsigned char buffer[SIZE], original[SIZE];

static void reset(void) {
    memset(buffer,0x90,sizeof(buffer));
    memcpy(buffer+MESSAGE_AT,message,sizeof(message));
}

/* One assertion site at `at`: cmp (ends with the imm8 0), jne over the message, 8 bytes of the
 * (dead) assertion path, then `lea reg,[rip+message]` and the code the jne goes to. Returns the
 * offset of the jne. */
static size_t site(size_t at, const unsigned char *cmp, size_t cmp_length, int lea_register) {
    memcpy(buffer+at,cmp,cmp_length);
    size_t jne=at+cmp_length;
    memset(buffer+jne+2,0xcc,8);
    size_t lea=jne+2+8;
    buffer[lea]=0x48; buffer[lea+1]=0x8d; buffer[lea+2]=(unsigned char)(0x05|lea_register<<3);
    int32_t rel=(int32_t)((int64_t)MESSAGE_AT-(int64_t)(lea+7));
    memcpy(buffer+lea+3,&rel,4);
    buffer[jne]=0x75; buffer[jne+1]=(unsigned char)(2+8+7-2);   /* to just after the lea */
    return jne;
}

static void run(void) {
    memcpy(original,buffer,sizeof(buffer));
    image=buffer;
    patch_eop_tick_wait(SIZE);
}

/* The 4 bytes after the jne became pause; jmp short back to the cmp; nothing else changed. */
static void expect_patched(size_t cmp_at, size_t jne) {
    assert(buffer[jne+2]==0xf3 && buffer[jne+3]==0x90 && buffer[jne+4]==0xeb);
    assert((int64_t)(jne+6)+(int8_t)buffer[jne+5]==(int64_t)cmp_at);
    for (size_t i=0;i<SIZE;++i)
        if (i<jne+2 || i>=jne+6) assert(buffer[i]==original[i]);
}

static void expect_unchanged(void) { assert(!memcmp(buffer,original,SIZE)); }

int main(void) {
    /* 1.00 shape: cmp qword [rax+0xa08], 0 (mod 10, no SIB) with lea rdi */
    static const unsigned char disp32[]={0x48,0x83,0xb8,0x08,0x0a,0,0,0x00};
    /* US 1.02 shape: cmp qword [rax+rcx+0xa08], 0 (mod 10, SIB) */
    static const unsigned char disp32_sib[]={0x48,0x83,0xbc,0x08,0x08,0x0a,0,0,0x00};
    /* disp8 forms, without and with SIB, and a REX.WB base register */
    static const unsigned char disp8[]={0x48,0x83,0x78,0x10,0x00};
    static const unsigned char disp8_sib[]={0x48,0x83,0x7c,0x08,0x10,0x00};
    static const unsigned char rex_b[]={0x49,0x83,0xbf,0x08,0x0a,0,0,0x00};
    struct { const unsigned char *cmp; size_t length; } shapes[]={
        {disp32,sizeof(disp32)},{disp32_sib,sizeof(disp32_sib)},{disp8,sizeof(disp8)},
        {disp8_sib,sizeof(disp8_sib)},{rex_b,sizeof(rex_b)}};

    /* every accepted shape, alone, with lea rdi (register 7) */
    for (size_t s=0;s<sizeof(shapes)/sizeof(*shapes);++s) {
        reset();
        size_t jne=site(0x100,shapes[s].cmp,shapes[s].length,7);
        run();
        expect_patched(0x100,jne);
    }
    /* all of them in one image: the matcher patches each site, not only the first */
    reset();
    size_t jnes[5];
    for (size_t s=0;s<5;++s) jnes[s]=site(0x80*(s+1),shapes[s].cmp,shapes[s].length,7);
    memcpy(original,buffer,sizeof(buffer)); image=buffer; patch_eop_tick_wait(SIZE);
    for (size_t s=0;s<5;++s) {
        assert(buffer[jnes[s]+2]==0xf3 && buffer[jnes[s]+3]==0x90 && buffer[jnes[s]+4]==0xeb);
        assert((int64_t)(jnes[s]+6)+(int8_t)buffer[jnes[s]+5]==(int64_t)(0x80*(s+1)));
    }

    /* negative: a cmp [mem],0 and jne, but no assertion path (no lea of the message) after it:
     * no trap to guard, so nothing may change */
    reset();
    memcpy(buffer+0x100,disp32,sizeof(disp32));
    buffer[0x100+sizeof(disp32)]=0x75; buffer[0x100+sizeof(disp32)+1]=0x0a;
    run();
    expect_unchanged();

    /* negative: the image has no message at all */
    reset();
    site(0x100,disp32,sizeof(disp32),7);
    memset(buffer+MESSAGE_AT,'x',sizeof(message));
    run();
    expect_unchanged();

    /* negative: lea points at the message but nothing before it is a cmp [mem],0 */
    reset();
    size_t lea=0x100+10;
    buffer[lea]=0x48; buffer[lea+1]=0x8d; buffer[lea+2]=0x3d;
    int32_t rel=(int32_t)((int64_t)MESSAGE_AT-(int64_t)(lea+7));
    memcpy(buffer+lea+3,&rel,4);
    run();
    expect_unchanged();

    /* negative: the jne target lies before the message reference (a loop, not a skip) */
    reset();
    size_t jne=site(0x100,disp32,sizeof(disp32),7);
    buffer[jne+1]=0xf0;
    run();
    expect_unchanged();

    /* negative: no room for the 4 patched bytes between the jne and the lea */
    reset();
    memcpy(buffer+0x100,disp32,sizeof(disp32));
    jne=0x100+sizeof(disp32);
    buffer[jne]=0x75; buffer[jne+1]=0x0a;
    lea=jne+2+2;
    buffer[lea]=0x48; buffer[lea+1]=0x8d; buffer[lea+2]=0x3d;
    rel=(int32_t)((int64_t)MESSAGE_AT-(int64_t)(lea+7));
    memcpy(buffer+lea+3,&rel,4);
    run();
    expect_unchanged();

    puts("eop matcher tests passed");
    return 0;
}
