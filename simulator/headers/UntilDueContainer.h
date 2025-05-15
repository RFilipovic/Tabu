#ifndef UNTILDUECONTAINER_H
#define UNTILDUECONTAINER_H

#include "Container.h"

class UntilDue {
    public:
        UntilDue();
        UntilDue(int minutes, int seconds);
        void setMinutes(int minutes);
        int getMinutes();
        void setSeconds(int seconds);
        int getSeconds();
        std::string toString() const;
    private:
        int minutes;
        int seconds;
};

class UntilDueContainer : public Container {
    public:
        UntilDueContainer();
        UntilDueContainer(const std::string &id, const UntilDue &untilDue);
        void displayDetails() const;
        std::string getDetails() const;
        UntilDue getUntilDue() const;
        void setUntilDue(UntilDue &newUntilDue);
        std::string getId() const;
    private:
        UntilDue untilDue;
};

#endif //UNTILDUECONTAINER_H