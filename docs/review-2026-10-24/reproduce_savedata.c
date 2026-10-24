/* Synthetic fixtures only. Run from the repository root; see README.md. */
#include "../../src/runtime_savedata.c"
#include <assert.h>
static char fixture_root[128];
const char *runtime_file_user_dir(void) { return fixture_root; }
int runtime_file_mount(const char *a,const char *b) { (void)a;(void)b;return 0; }
void runtime_file_unmount(const char *a) { (void)a; }
uintptr_t runtime_lookup(const RuntimeExport *t,size_t n,const char *s) {
    (void)t;(void)n;(void)s;return 0;
}
int main(void) {
    strcpy(fixture_root,"/tmp/uncharted-review-XXXXXX"); assert(mkdtemp(fixture_root));
    save_initialize(NULL);
    DirName name={"real"}; MountResult mounted;
    assert(!mount(1,"TEST",&name,MODE_CREATE,&mounted));
    MountPoint invalid={"/savedataX"};
    printf("invalid mount alias resolves to slot %d (expected -1)\n",slot_of(&invalid));
    assert(slot_of(&invalid)==0);
    char base[600], stray[700]; root(1,"TEST",base,sizeof(base));
    snprintf(stray,sizeof(stray),"%s/stray.txt",base);
    FILE *f=fopen(stray,"wb");assert(f);fclose(f);
    TitleId title={"TEST"}; SearchCond cond={.user=1,.title=&title};
    DirName names[8]; SearchResult result={.names=names,.names_capacity=8};
    assert(!save_search(&cond,&result));
    printf("save search reports %u hits (expected 1 directory)\n",result.hits);
    assert(result.hits==2);
    char protected_file[800];snprintf(protected_file,sizeof(protected_file),"%s/real/child",base);
    f=fopen(protected_file,"wb");assert(f);fclose(f);
    assert(!chmod(slots[0].host,0500));
    Delete del={.user=1,.title=&title,.dir=&name}; int rc=save_delete(&del);
    printf("delete returned %d; file still exists=%d (expected error)\n",rc,access(protected_file,F_OK)==0);
    assert(rc==0 && access(protected_file,F_OK)==0);
    chmod(slots[0].host,0700);remove_tree(fixture_root);
}
