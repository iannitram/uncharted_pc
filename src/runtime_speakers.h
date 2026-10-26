/* The speaker layout the games are told and the 7.1 fold-down, as pure functions (no SDL), so
 * tests/test_speakers.c checks them on their own. Used by runtime_audio.c. */
#ifndef RUNTIME_SPEAKERS_H
#define RUNTIME_SPEAKERS_H
#include <string.h>

/* Channels the games are told (and the 8-channel ports are mixed to): 2, 6 (5.1) or 8 (7.1).
 * `mode`: BB_SPEAKERS (launcher's Speakers setting): stereo/2, 5.1/6, 7.1/8; anything else is
 * auto. `force_stereo`: BB_AUDIO_STEREO is set (the Linux fork's switch, kept: it wins over
 * everything). `device`: channels of the default output device, 0 when there is none. Auto
 * follows the device: 8 or more is 7.1, 6 or 7 is 5.1, anything less (a stereo device, the Steam
 * Deck's speakers, no device) is stereo. */
static inline int runtime_speaker_layout(const char *mode, int force_stereo, int device) {
    if (force_stereo) return 2;
    if (mode && (!strcmp(mode,"2") || !strcmp(mode,"stereo"))) return 2;
    if (mode && (!strcmp(mode,"6") || !strcmp(mode,"5.1"))) return 6;
    if (mode && (!strcmp(mode,"8") || !strcmp(mode,"7.1"))) return 8;
    return device>=8 ? 8 : device>=6 ? 6 : 2;
}

/* One frame of the game's 7.1 mix (SDL order: FL FR FC LFE BL BR SL SR) folded to `n` channels
 * (2, 6 or 8) in `o`: stereo gets FL/FR at full level and centre and surrounds at -3 dB (LFE
 * dropped, not scaled down by SDL's 0.3); 5.1 keeps FL FR FC LFE and adds the back pair to the
 * sides at -3 dB; 8 is unchanged. Samples are clamped to [-1, 1]. */
static inline void runtime_fold_frame(const float s[8], int n, float o[8]) {
    if (n==6) { o[0]=s[0]; o[1]=s[1]; o[2]=s[2]; o[3]=s[3]; o[4]=s[6]+0.7071f*s[4]; o[5]=s[7]+0.7071f*s[5]; }
    else if (n==2) { o[0]=s[0]+0.7071f*(s[2]+s[4]+s[6]); o[1]=s[1]+0.7071f*(s[2]+s[5]+s[7]); }
    else { for (int c=0;c<8;++c) o[c]=s[c]; n=8; }
    for (int c=0;c<n;++c) o[c]=o[c]>1.0f ? 1.0f : o[c]<-1.0f ? -1.0f : o[c];
}
#endif
