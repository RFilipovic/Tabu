#ifndef SIMULATOR_H
#define SIMULATOR_H

#include "SingleContainerCrane.h"
#include "Printer.h"
#include "ParsedBuffers.h"

class HotStorageSimulator {
public:
    HotStorageSimulator(Printer &p);
    void simulate();
private:
    Printer *printer;
    void runEntryStack();
    void runCrane();
    void runOutgoingStack();
};

#endif //SIMULATOR_H