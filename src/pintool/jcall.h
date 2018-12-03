#include <iostream>
#include <fstream>
#include <stdlib.h>
#include "pin.H"

#include "utils/fn_bound.h"
#include "utils/plt.h"
#include "utils/lib.h"

/* Out file to store results */
ofstream jcall_ofile; 

/* Do we keep tracking in libraries? */
bool jcall_lib;

/* Function table */
fn_bound_t **JCALL_FN_TABLE;

void jcall_call(ADDRINT target, string *ins, ADDRINT rip) {
    if (!jcall_lib && is_lib(target) && is_lib(rip))
        return;
    fn_bound_t *f = fn_add(JCALL_FN_TABLE, "", target, target);
    f->calls += 1;
    if (ins)
        f->ins = add_ins(f->ins, ins, rip);
}

/* Instrument every instruction to check discontinuity */
void jcall_instrument_instruction(INS ins, void *v) {
    string *ins_str = NULL;
    ins_str = new string(INS_Disassemble(ins));
    if (INS_IsCall(ins)) {
        if (INS_IsDirectCall(ins)) {
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) jcall_call,
                    IARG_ADDRINT,
                    INS_DirectBranchOrCallTargetAddress(ins),
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        } else {
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) jcall_call,
                    IARG_BRANCH_TARGET_ADDR,
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        }
    }
    if (!is_plt_or_pltgot(INS_Address(ins)) && jmp_from_plt_or_pltgot(ins))
        INS_InsertCall(ins,
                        IPOINT_BEFORE,
                        (AFUNPTR) jcall_call, 
                        IARG_BRANCH_TARGET_ADDR,
                        IARG_PTR, ins_str,
                        IARG_ADDRINT, INS_Address(ins),
                        IARG_END);
}

void jcall_instrument_image(IMG img, void *v) {
    for (SEC sec = IMG_SecHead(img); SEC_Valid(sec); sec = SEC_Next(sec)) {
        if (SEC_Name(sec) == ".plt") {
            ADDRINT start = SEC_Address(sec);
            ADDRINT end = start + SEC_Size(sec);
            add_plt(start, end);
        }
        if (SEC_Name(sec) == ".plt.got") {
            ADDRINT start = SEC_Address(sec);
            ADDRINT end = start + SEC_Size(sec);
            add_pltgot(start, end);
        }
    }
}

/* Handler called at the end of the execution */
void jcall_over(INT32 code, void *v, float elapsed) {
    jcall_ofile << elapsed << endl;
    /* Print relevant information */
    for (int i = 0; i < TABLE_SIZE; i++) {
        fn_bound_t *f = JCALL_FN_TABLE[i];
        while (f) {
            if (f->img_name == NULL) {
                f->img_name = new string("");
                PIN_LockClient();
                IMG img = IMG_FindByAddress(f->entry);
                PIN_UnlockClient();
                if (IMG_Valid(img)) {
                    f->img_name = new string(IMG_Name(img));
                    f->offset = f->entry - IMG_LoadOffset(img);
                }
            }
            fn_print_one(jcall_ofile, f);
            f = f->next;
        }
    }

    /* Close the log file */
    jcall_ofile.close();
}

void jcall_init(string pgm, string odir, bool _lib) {
    jcall_lib = _lib;
    jcall_ofile.open((odir + pgm + "_jcall.txt").c_str());
    JCALL_FN_TABLE = fn_init_table();
}
