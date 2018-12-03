#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <list>
#include "pin.H"

#include <sys/time.h>

#include "utils/fn_bound.h"
#include "utils/plt.h"
#include "utils/ins.h"
#include "utils/lib.h"

#define RECORD_INS 0

/* Do we keep tracking in libraries? */
bool oracle_lib;

/* In file to get function boundaries */
ifstream ifile;

/* Out file to store results */
ofstream oracle_ofile; 

/* Function table */
fn_bound_t **ORACLE_FN_TABLE;

/* Previous value of RIP */
ADDRINT prev_rip;
/* String of the disassembled previous instruction */
string *prev_ins;
/* Expected next value of RIP */
ADDRINT expected_rip;

/* Detect discontinuity in RIP */
void check_continuity(ADDRINT curr_rip, ADDRINT next_rip, string *ins) {
    if (!oracle_lib && is_lib(curr_rip) && is_lib(prev_rip))
        goto save;
    /* If the current value of RIP is not what expected, 
       it means there was a discontinuity */
    if (curr_rip != expected_rip && expected_rip != 0) {
        /* If it is a discontinuity from plt to plt, we ignore it */
        if (!is_plt_or_pltgot(curr_rip) || !is_plt_or_pltgot(prev_rip)) {
            /* Check if current RIP corresponds to an entry point */
            fn_bound_t *f = fn_find(ORACLE_FN_TABLE, curr_rip);
            /* If yes */
            if (f) {
                /* Increase total number of calls */
                f->calls += 1;
                /* And log instructon that led to this call */
                if (prev_ins) {
                    f->ins = add_ins(f->ins, prev_ins, prev_rip);
                }   
            }
        }
    }
save:
    /* Save value of RIP for next iteration */
    prev_rip = curr_rip;
    /* Save disassembly of current instruction for next iteration */
    prev_ins = ins;
    /* Save expected next value of RIP */
    expected_rip = next_rip;
    return;
}

void oracle_save(ADDRINT rip, string *ins) {
    prev_rip = rip; 
    prev_ins = ins;
}

void oracle_call(ADDRINT rip) {
    PIN_LockClient();
    IMG curr_img = IMG_FindByAddress(rip);
    IMG prev_img = IMG_FindByAddress(prev_rip);
    PIN_UnlockClient();
    if (!oracle_lib && (!IMG_Valid(curr_img) || !IMG_IsMainExecutable(curr_img))
            && ((!IMG_Valid(prev_img) || !IMG_IsMainExecutable(prev_img)))) {
        return;
    }
    if (!is_plt_or_pltgot(rip) || !is_plt_or_pltgot(prev_rip)) {
        /* Check if current RIP corresponds to an entry point */
        fn_bound_t *f = fn_find(ORACLE_FN_TABLE, rip);
        /* If yes */
        if (f) {
            /* Increase total number of calls */
            f->calls += 1;
            /* And log instructon that led to this call */
            if (prev_ins) {
                f->ins = add_ins(f->ins, prev_ins, prev_rip);
            }   
        }
    }
}        

/* Instrument every routine to get its boundaries */
void oracle_instrument_routine(RTN rtn, void *V) {
    if (!oracle_lib)
        return;
    RTN_Open(rtn);
    RTN_InsertCall(
                rtn, 
                IPOINT_BEFORE, 
                (AFUNPTR) fn_add, 
                IARG_PTR, ORACLE_FN_TABLE,
                IARG_PTR, RTN_Name(rtn).c_str(),
                IARG_ADDRINT, RTN_Address(rtn),
                IARG_ADDRINT, RTN_Address(rtn) + RTN_Size(rtn),
                IARG_END);
    RTN_Close(rtn);
}

/* Instrument every image to get plt & plt.got addresses */
void oracle_instrument_image(IMG img, void *v) {
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

/* Instrument every instruction to check discontinuity */
void oracle_instrument_instruction(INS ins, void *v) {
#if 0
    IMG img = IMG_FindByAddress(INS_Address(ins));
    if (!lib && (!IMG_Valid(img) || !IMG_IsMainExecutable(img))) {
        return;
    }
#endif
    string *ins_str = NULL;
    ins_str = new string(INS_Disassemble(ins));
#if 0
    INS_InsertCall(
                ins, 
                IPOINT_BEFORE, 
                (AFUNPTR) check_continuity,
                IARG_ADDRINT,
                /* Current instruction address */
                INS_Address(ins),
                IARG_ADDRINT,
                /* Next instruction address (sequentially) */
                INS_NextAddress(ins),
                IARG_PTR, ins_str,
                IARG_END);
#else
    if (fn_find(ORACLE_FN_TABLE, INS_Address(ins))) {
        INS_InsertCall(
                ins, 
                IPOINT_BEFORE, 
                (AFUNPTR) oracle_call,
                IARG_ADDRINT,
                /* Current instruction address */
                INS_Address(ins),
                IARG_END);
    }
    INS_InsertCall(
                ins, 
                IPOINT_BEFORE, 
                (AFUNPTR) oracle_save, 
                IARG_ADDRINT, INS_Address(ins),
                IARG_PTR, ins_str,
                IARG_END);
#endif
}

/* Handler called at the end of the execution */
void oracle_over(INT32 code, void *v, float elapsed) {
    oracle_ofile << elapsed << endl;
    for (int i = 0; i < TABLE_SIZE; i++) {
    /* Print relevant information */
        fn_bound_t *f = ORACLE_FN_TABLE[i];
        while (f) {
            if (f->img_name == NULL)
                f->img_name = new string("");
            fn_print_one(oracle_ofile, f);
            f = f->next;
        }
    }
    /* Close the log file */
    oracle_ofile.close();
}

string read_part(ifstream &ifile) {
    string part = "";
    char m;
    while (ifile) {
        ifile.read(&m, 1);
        if (m == ':' || m == '\n')
            return part;
        else 
            part += m;
    }
    return part;
}

/* Parse function boundaries from the file given in parameter */
void ParseBoundaries(void) {
    while (ifile) {
        string fname = read_part(ifile);
        ADDRINT entry = atol(read_part(ifile).c_str()); 
        ADDRINT ret = atol(read_part(ifile).c_str()); 
        if (entry != 0 and ret != 0)
            fn_add(ORACLE_FN_TABLE, fname, entry, ret);
    }
}

void oracle_init(string pgm, string ifile_path, string odir, bool _lib) {
    ifile.open((ifile_path).c_str());
    oracle_lib = _lib;
    oracle_ofile.open((odir + pgm + "_oracle.txt").c_str());
    expected_rip = 0;
    ORACLE_FN_TABLE = fn_init_table();
    ParseBoundaries();
}


