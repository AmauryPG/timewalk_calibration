#pragma once

#include <iostream>
#include <fstream>
#include <vector>
#include <memory>
#include <string>
#include <math.h>
#include <algorithm>
#include <filesystem>

#include <pybind11/embed.h>
#include <pybind11/numpy.h>

#include "../../displayHandler.h"

#pragma GCC visibility push(hidden)
class pythonInterface
{
private:
    // Interpreter lives for lifetime of PythonCaller
    pybind11::scoped_interpreter guard{};
    pybind11::module_ script;
    displayHandler *m_displayHandler = nullptr;

    template <typename... Args>
    pybind11::object callPythonFunction(const std::string &funcName, Args &&...args)
    {
        try
        {
            pybind11::object func = script.attr(funcName.c_str());
            return func(std::forward<Args>(args)...);
        }
        catch (const pybind11::error_already_set &e)
        {
            std::cerr << "Python error calling '" << funcName << "': " << e.what() << std::endl;
        }
        return pybind11::none();
    }

public:
    pythonInterface(displayHandler *displayHandler);
    ~pythonInterface();

    bool readBinaryFile(std::string pathToBinaryFile, double *&tof, double *&energy, size_t &eventSize);
};