#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <list>
#include "pin.H"

#include <sys/time.h>

#include "utils/fn_bound.h"
#include "utils/plt.h"
#include "utils/call_stack.h"
#include "utils/bintree.h"
#include "utils/lib.h"

#define CHECK_CROSS_BOUNDARIES 1

/* Out file to store results */
ofstream iCi_ofile; 

/* Do we keep tracking in libraries? */
bool iCi_lib;

/* Function table */
fn_bound_t **TCALL_FN_TABLE;

/* Jmp pruned table */
fn_bound_t **TCALL_PRUNED_JMP;

/* Binary tree of entry points */
node_t *TCALL_BINTREE;
/* Pruned jumps */
node_t *PRUNED_JMP = bintree_init(0);

void iCi_call(ADDRINT target, ADDRINT retaddr, ADDRINT rsp, string *ins, ADDRINT rip) {
    if (!iCi_lib && is_lib(target) && is_lib(rip))
        return;
    // cs_call(target, retaddr, rsp - 8);
    fn_bound_t *f = fn_add(TCALL_FN_TABLE, "", target, target);
#if CHECK_CROSS_BOUNDARIES
    if (fn_created()) {
        if (!TCALL_BINTREE)
            TCALL_BINTREE = bintree_init(target);
        else {
            bintree_insert(TCALL_BINTREE, target);
            fn_flush(TCALL_PRUNED_JMP);
        }
    }
#endif
    f->calls += 1;
    if (ins)
        f->ins = add_ins(f->ins, ins, rip);
}

void iCi_jmp(ADDRINT target, ADDRINT retaddr, ADDRINT rsp, string *ins, ADDRINT rip) {
    /* Entry corresponding to the last detected call */
    call_entry_t *top = cs_top();
    fn_bound_t *top_fn = NULL;
    if (top)
        /* Get function object corresponding to the last call */
        top_fn = fn_find(TCALL_FN_TABLE, top->calladdr);
    fn_bound_t *jmp_entry = fn_find(TCALL_PRUNED_JMP, rip);
    if (jmp_entry && jmp_entry->ret)
        return;

    /* Exclusion checks */
    if (
                /* From plt to plt => ignore */
                   (is_plt_or_pltgot(target) && is_plt_or_pltgot(rip))
                /* Stack is not in the same state as it was at the entry point */
                || (top && rsp != top->rsp)
                /* Jump between entry point and current position */
                || (top && top->calladdr <= target && target <= rip)
                /* Jump between current position and known return address of function */
                || (top_fn && top_fn->ret >= target && target >= rip)
            ) {
#if 0
        bintree_insert(PRUNED_JMP, target);
#endif
        fn_add(TCALL_PRUNED_JMP, "", rip, target);
        return;
    }
    /* Inclusion checks */
    if (
                /* Jump to a known entry point */
                fn_find(TCALL_FN_TABLE, target) 
                /* Jump to an address lower than the entry point */
                || (top && target <= top->calladdr)
                /* Jump to an address higher than the ret point */
                // || (top_fn && target >= top_fn->ret && target >= rip)
#if CHECK_CROSS_BOUNDARIES
                || bintree_search_between(TCALL_BINTREE, MIN(target, rip), MAX(target, rip))
#endif
            ) {
        iCi_call(target, retaddr, rsp + 8, ins, rip);
        return;
    }
    fn_add(TCALL_PRUNED_JMP, "", rip, rip);

    // default policy
    // call(target, retaddr, rsp + 8, ins, rip);
}

void iCi_ret(ADDRINT rip, ADDRINT addr) {
#if 0
    if (!TCALL_BINTREE)
        TCALL_BINTREE = bintree_init(addr);
    else
        bintree_insert(TCALL_BINTREE, addr);
#endif
    cs_ret(TCALL_FN_TABLE, rip, addr);
    return;
}

BOOL dont_prune(node_t *tree, ADDRINT target) {
    return !bintree_search(tree, target);
}

/* Instrument every instruction to check discontinuity */
void iCi_instrument_instruction(INS ins, void *v) {
    string *ins_str = new string(INS_Disassemble(ins));
    if (INS_IsCall(ins)) {
        if (INS_IsDirectCall(ins)) {
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) iCi_call,
                    IARG_ADDRINT,
                    INS_DirectBranchOrCallTargetAddress(ins),
                    IARG_ADDRINT, INS_NextAddress(ins),
                    IARG_REG_VALUE, REG_RSP,
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        } else {
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) iCi_call,
                    IARG_BRANCH_TARGET_ADDR,
                    IARG_ADDRINT, INS_NextAddress(ins),
                    IARG_REG_VALUE, REG_RSP,
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        }
    }
#if 0
    else if (!is_plt_or_pltgot(INS_Address(ins)) && jmp_from_plt_or_pltgot(ins))
        INS_InsertCall(ins,
                        IPOINT_BEFORE,
                        (AFUNPTR) iCi_call,
                        IARG_BRANCH_TARGET_ADDR,
                        IARG_ADDRINT, INS_NextAddress(ins),
                        IARG_REG_VALUE, REG_RSP,
                        IARG_PTR, ins_str,
                        IARG_ADDRINT, INS_Address(ins),
                        IARG_END);
#endif
    else if (INS_IsBranchOrCall(ins) 
                && ((INS_Category(ins) == XED_CATEGORY_UNCOND_BR)
                || (INS_IsDirectBranch(ins) && INS_Category(ins) == XED_CATEGORY_COND_BR)
            )) {
        if (INS_IsDirectBranchOrCall(ins)) {
#if 0
            INS_InsertIfCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) dont_prune, 
                    IARG_ADDRINT, PRUNED_JMP,
                    IARG_ADDRINT, INS_DirectBranchOrCallTargetAddress(ins),
                    IARG_END);
            INS_InsertThenCall(
#else
            INS_InsertCall(
#endif
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) iCi_jmp,
                    IARG_ADDRINT,
                    INS_DirectBranchOrCallTargetAddress(ins),
                    IARG_ADDRINT, INS_NextAddress(ins),
                    IARG_REG_VALUE, REG_RSP,
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
        } else
            INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) iCi_jmp,
                    IARG_BRANCH_TARGET_ADDR,
                    IARG_ADDRINT, INS_NextAddress(ins),
                    IARG_REG_VALUE, REG_ESP,
                    IARG_PTR, ins_str,
                    IARG_ADDRINT, INS_Address(ins),
                    IARG_END);
    }
#if 1
    if (INS_IsRet(ins)) {
        INS_InsertCall(ins,
                        IPOINT_BEFORE,
                        (AFUNPTR) iCi_ret, 
                        IARG_ADDRINT, INS_Address(ins),
                        IARG_BRANCH_TARGET_ADDR,
                        IARG_END);
    }
#endif
}

void iCi_instrument_image(IMG img, void *v) {
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
void iCi_over(INT32 code, void *v, float elapsed) {
    iCi_ofile << elapsed << endl;
    /* Print relevant information */
    for (int i = 0; i < TABLE_SIZE; i++) {
        fn_bound_t *f = TCALL_FN_TABLE[i];
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
            fn_print_one(iCi_ofile, f);
            f = f->next;
        }
    }

    // bintree_stats(TCALL_BINTREE);
    /* Close the log file */
    iCi_ofile.close();
}

void iCi_init(string pgm, string odir, bool _lib) {
    iCi_ofile.open((odir + pgm + "_iCi.txt").c_str());
    TCALL_FN_TABLE = fn_init_table();
    TCALL_PRUNED_JMP = fn_init_table();
    TCALL_BINTREE = bintree_init(0x6fffff);
    iCi_lib = _lib;
    return;
}

