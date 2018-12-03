#include <sys/time.h>
#include "pin.H"

#ifdef PEMPTY
    #include "empty.h"
#endif

#ifdef ORACLE
    #include "oracle.h"
#endif

#ifdef JCALL
    #include "jcall.h"
#endif

#ifdef JMP
    #include "jmp.h"
#endif

#ifdef ICI
    #include "iCi.h"
#endif

/* Time of instrumentation */
struct timeval start, stop; 

/* Out directory to store analysis results */
string odir;
KNOB<string> KnobOutputDir(KNOB_MODE_WRITEONCE, "pintool", "o", "/dev/null", "Specify an output directory");
/* Instrument libraries ?*/
bool _lib;
KNOB<string> KnobLib(KNOB_MODE_WRITEONCE, "pintool", "l", "false", "Follow libraries?");
/* Name of the program to analyze */
string pgm;
KNOB<string> KnobPgmName(KNOB_MODE_WRITEONCE, "pintool", "p", "/dev/null", "Program basename");

#ifdef ORACLE
    string ifilepath;
    KNOB<string> KnobInputFile(KNOB_MODE_WRITEONCE, "pintool", "i", "/dev/null", "Specify an input file");
#endif

/* Instrument every instruction to check discontinuity */
void instrument_instruction(INS ins, void *v) {
#ifdef ORACLE
    oracle_instrument_instruction(ins, v);
#endif
#ifdef JCALL
    jcall_instrument_instruction(ins, v);
#endif
#ifdef JMP
    jmp_instrument_instruction(ins, v);
#endif
#ifdef ICI
    iCi_instrument_instruction(ins, v);
#endif
    return;
}

void instrument_image(IMG img, void *v) {
#ifdef ORACLE
    oracle_instrument_image(img, v);
#endif
#ifdef JCALL
    jcall_instrument_image(img, v);
#endif
#ifdef ICI
    iCi_instrument_image(img, v);
#endif
    return;
}

void instrument_routine(RTN rtn, void *v) {
#ifdef ORACLE
    oracle_instrument_routine(rtn, v);
#endif
    return;
}

/* Handler called at the end of the execution */
void over(INT32 code, void *v) {
    gettimeofday(&stop, NULL);

    float elapsed = (stop.tv_usec / 1000.0 + 1000 * stop.tv_sec - start.tv_sec * 1000 - start.tv_usec / 1000.0) / 1000.0;

#ifdef PEMPTY
    empty_over(code, v, elapsed);
#endif
#ifdef ORACLE
    oracle_over(code, v, elapsed);
#endif
#ifdef JCALL
    jcall_over(code, v, elapsed);
#endif
#ifdef JMP
    jmp_over(code, v, elapsed);
#endif
#ifdef ICI
    iCi_over(code, v, elapsed);
#endif
    return;
}

int main(int argc, char * argv[]) {

    PIN_SetSyntaxIntel();
    PIN_InitSymbolsAlt(DEBUG_OR_EXPORT_SYMBOLS);

    if (PIN_Init(argc, argv)) return 1;

    odir = KnobOutputDir.Value().c_str();
    pgm = KnobPgmName.Value();

    _lib = (KnobLib.Value() == "true");

#ifdef PEMPTY
    empty_init(pgm, odir);
#endif
#ifdef ORACLE
    ifilepath = KnobInputFile.Value().c_str();
    oracle_init(pgm, ifilepath, odir, _lib);
#endif
#ifdef JCALL
    jcall_init(pgm, odir, _lib);
#endif
#ifdef JMP
    jmp_init(pgm, odir, _lib);
#endif
#ifdef ICI
    iCi_init(pgm, odir, _lib);
#endif

    IMG_AddInstrumentFunction(instrument_image, 0);
    INS_AddInstrumentFunction(instrument_instruction, 0);
    RTN_AddInstrumentFunction(instrument_routine, 0);

    /* Register fini to be called when the
       application exits */
    PIN_AddFiniFunction(over, 0);

    gettimeofday(&start, NULL);

    PIN_StartProgram();

    return 0;
}
