#include <iostream>
#include <fstream>
#include <stdlib.h>
#include "pin.H"

#include "utils/fn_bound.h"
#include "utils/plt.h"
#include "utils/lib.h"

/* Out file to store results */
ofstream jmp_ofile; 

/* Do we keep tracking in libraries? */
bool jmp_lib;

/* Function table */
fn_bound_t **JMP_FN_TABLE;

void jmp_call(ADDRINT target, string *ins, ADDRINT rip) {
    if (!jmp_lib && is_lib(target) && is_lib(rip))
        return;
    fn_bound_t *f = fn_add(JMP_FN_TABLE, "", target, target);
    f->calls += 1;
    if (ins)
        f->ins = add_ins(f->ins, ins, rip);
}

/* Instrument every instruction to check discontinuity */
void jmp_instrument_instruction(INS ins, void *v) {
    string *ins_str = NULL;
    ins_str = new string(INS_Disassemble(ins));
    if (INS_IsCall(ins)) {
        if (INS_IsDirectCall(ins)) {
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) jmp_call,
                    IARG_ADDRINT,
                    INS_DirectBranchOrCallTargetAddress(ins),
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        } else {
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) jmp_call,
                    IARG_BRANCH_TARGET_ADDR,
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        }
    } else if (INS_IsBranchOrCall(ins) 
                && ((INS_Category(ins) == XED_CATEGORY_UNCOND_BR)
                || (INS_IsDirectBranch(ins) && INS_Category(ins) == XED_CATEGORY_COND_BR)
            )) {
        if (INS_IsDirectBranchOrCall(ins)) {
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) jmp_call,
                    IARG_ADDRINT,
                    INS_DirectBranchOrCallTargetAddress(ins),
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        } else
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) jmp_call, 
                    IARG_BRANCH_TARGET_ADDR,
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
    }
}

/* Handler called at the end of the execution */
void jmp_over(INT32 code, void *v, float elapsed) {
    jmp_ofile << elapsed << endl;
    /* Print relevant information */
    for (int i = 0; i < TABLE_SIZE; i++) {
        fn_bound_t *f = JMP_FN_TABLE[i];
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
            fn_print_one(jmp_ofile, f);
            f = f->next;
        }
    }

    /* Close the log file */
    jmp_ofile.close();
}

void jmp_init(string pgm, string odir, bool _lib) {
    jmp_ofile.open((odir + pgm + "_jmp.txt").c_str());
    jmp_lib = _lib;
    JMP_FN_TABLE = fn_init_table();
}

