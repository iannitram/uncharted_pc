#include "runtime_speakers.h"
#include <math.h>
#include <stdio.h>

static int failures;
#define CHECK(cond, what) do { if (!(cond)) { printf("FAIL: %s\n", what); ++failures; } } while (0)
#define NEAR(a, b) (fabsf((a)-(b)) < 1e-5f)

int main(void) {
    /* Auto follows the output device. */
    CHECK(runtime_speaker_layout(NULL,0,0)==2, "no device: stereo");
    CHECK(runtime_speaker_layout(NULL,0,1)==2, "mono device: stereo");
    CHECK(runtime_speaker_layout(NULL,0,2)==2, "stereo device (the Steam Deck's speakers): stereo");
    CHECK(runtime_speaker_layout(NULL,0,6)==6, "5.1 device: 5.1");
    CHECK(runtime_speaker_layout(NULL,0,7)==6, "6.1 device: 5.1");
    CHECK(runtime_speaker_layout(NULL,0,8)==8, "7.1 device: 7.1");
    CHECK(runtime_speaker_layout("auto",0,8)==8, "BB_SPEAKERS=auto follows the device");
    CHECK(runtime_speaker_layout("",0,6)==6, "empty BB_SPEAKERS follows the device");
    /* The launcher's Speakers setting wins over the device. */
    CHECK(runtime_speaker_layout("stereo",0,8)==2, "stereo on a 7.1 device");
    CHECK(runtime_speaker_layout("2",0,6)==2, "2 on a 5.1 device");
    CHECK(runtime_speaker_layout("5.1",0,2)==6, "5.1 on a stereo device");
    CHECK(runtime_speaker_layout("6",0,8)==6, "6 on a 7.1 device");
    CHECK(runtime_speaker_layout("7.1",0,2)==8, "7.1 on a stereo device");
    CHECK(runtime_speaker_layout("8",0,0)==8, "8 with no device");
    /* BB_AUDIO_STEREO (the Linux fork's switch) forces stereo over everything. */
    CHECK(runtime_speaker_layout(NULL,1,8)==2, "BB_AUDIO_STEREO on a 7.1 device");
    CHECK(runtime_speaker_layout("7.1",1,8)==2, "BB_AUDIO_STEREO beats BB_SPEAKERS");

    /* Fold-down: the games' stereo-only mix (front pair only) must come out at full level, not
       at the ~0.3 SDL's own 7.1 to stereo downmix gave. */
    const float front[8]={0.5f,-0.25f,0,0,0,0,0,0};
    float o[8];
    runtime_fold_frame(front,2,o);
    CHECK(NEAR(o[0],0.5f) && NEAR(o[1],-0.25f), "stereo fold keeps the front pair at full level");
    runtime_fold_frame(front,6,o);
    CHECK(NEAR(o[0],0.5f) && NEAR(o[1],-0.25f) && NEAR(o[2],0) && NEAR(o[3],0) && NEAR(o[4],0) && NEAR(o[5],0),
          "5.1 fold keeps the front pair");
    runtime_fold_frame(front,8,o);
    CHECK(NEAR(o[0],0.5f) && NEAR(o[1],-0.25f), "7.1 passes through");
    /* FL FR FC LFE BL BR SL SR */
    const float full[8]={0.1f,0.2f,0.4f,0.8f,0.1f,0.2f,0.3f,0.5f};
    runtime_fold_frame(full,2,o);
    CHECK(NEAR(o[0],0.1f+0.7071f*(0.4f+0.1f+0.3f)) && NEAR(o[1],0.2f+0.7071f*(0.4f+0.2f+0.5f)),
          "stereo fold adds centre and surrounds at -3 dB, drops LFE");
    runtime_fold_frame(full,6,o);
    CHECK(NEAR(o[2],0.4f) && NEAR(o[3],0.8f), "5.1 fold keeps centre and LFE");
    CHECK(NEAR(o[4],0.3f+0.7071f*0.1f) && NEAR(o[5],0.5f+0.7071f*0.2f), "5.1 fold adds the back pair to the sides at -3 dB");
    runtime_fold_frame(full,8,o);
    for (int c=0;c<8;++c) CHECK(NEAR(o[c],full[c]), "7.1 unchanged");
    /* Clamping. */
    const float loud[8]={0.9f,-0.9f,0.9f,0,0.9f,0.9f,0.9f,0.9f};
    runtime_fold_frame(loud,2,o);
    CHECK(NEAR(o[0],1.0f) && NEAR(o[1],-0.9f+0.7071f*(0.9f+0.9f+0.9f)>1.0f ? 1.0f : -0.9f+0.7071f*(0.9f+0.9f+0.9f)), "stereo fold clamps");
    runtime_fold_frame(loud,6,o);
    CHECK(NEAR(o[4],1.0f) && NEAR(o[5],1.0f), "5.1 fold clamps");
    printf(failures ? "speakers: %d failed\n" : "speakers: all checks passed\n", failures);
    return failures!=0;
}
