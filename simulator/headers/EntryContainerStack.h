#ifndef ENTRYCONTAINERSTACK_H
#define ENTRYCONTAINERSTACK_H

#include <iostream>
#include <string>
#include <chrono>
#include <cstdlib>
#include "Buffer.h"
#include "UntilDueContainer.h"

class EntryContainerStack : public Buffer {
private:
    int containerId; 
    int pauseFlag;
public:
    EntryContainerStack();
    void startAutoAddContainers(int iterations, double delayInSeconds);
    void pauseTime();
    void continueTime();
    int &getPauseFlag();
};

#endif // ENTRYCONTAINERSTACK_H
