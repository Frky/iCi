#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <list>
#include "pin.H"

#include <sys/time.h>

#include "utils/fn_bound.h"

/* Out file to store analysis results */
ofstream ofile;
KNOB<string> KnobOutputFile(KNOB_MODE_WRITEONCE, "pintool", "o", "/dev/null", "Specify an output file");

/* Time of instrumentation */
struct timeval start, stop; 

VOID call(ADDRINT target) {
    fn_bound_t *f = find_table(target);
    if (!f)
        f = add_function("", target, target);
    f->calls += 1;
}

/* Instrument every instruction to check discontinuity */
VOID instrument_instruction(INS ins, VOID *v) {
    if (INS_IsDirectCall(ins)) {
        INS_InsertCall(
                    ins, 
                    IPOINT_BEFORE, 
                    (AFUNPTR) call,
                    IARG_ADDRINT,
                    /* Target of the direct call */
                    INS_DirectBranchOrCallTargetAddress(ins),
                    IARG_END);
    }
}

/* Handler called at the end of the execution */
VOID over(INT32 code, VOID *v) {
    gettimeofday(&stop, NULL);

    ofile << "online time:" << (stop.tv_usec / 1000.0 + 1000 * stop.tv_sec - start.tv_sec * 1000 - start.tv_usec / 1000.0) / 1000.0 << endl;

    /* Print relevant information */
    for (int i = 0; i < TABLE_SIZE; i++) {
        fn_bound_t *f = FN_TABLE[i];
        while (f) {
            ofile << *(f->img_name) << ":" << f->offset << ":" << *(f->name) << ":" << f->calls << endl;
            f = f->next;
        }
    }
    /* Close the log file */
    ofile.close();
}

int main(int argc, char * argv[]) {

    PIN_SetSyntaxIntel();
    PIN_InitSymbolsAlt(DEBUG_OR_EXPORT_SYMBOLS);

    if (PIN_Init(argc, argv)) return 1;

    // We need to open this file early (even though
    // it is only needed in the end) because PIN seems
    // to mess up IO at some point
    ofile.open(KnobOutputFile.Value().c_str());

    INS_AddInstrumentFunction(instrument_instruction, 0);

    /* Register fini to be called when the
       application exits */
    PIN_AddFiniFunction(over, 0);

    init_table();

    gettimeofday(&start, NULL);

    PIN_StartProgram();

    return 0;
}

