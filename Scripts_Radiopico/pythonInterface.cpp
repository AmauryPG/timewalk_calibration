#include "pythonInterface.h"

pythonInterface::pythonInterface(displayHandler *dh)
{
    if (dh == nullptr)
    {
        throw std::runtime_error("[pythonInterface] Display handler is null, this is not allow.");
    }
    
    m_displayHandler = dh;

    try
    {
        m_displayHandler->messageInfo("Initializing Python environment...");
        // Get path to python relative to executable
        std::filesystem::path exe_path = std::filesystem::current_path(); // assuming executable runs in build/
        std::filesystem::path scripts_path = std::filesystem::absolute(exe_path / ".." / "src" / "python" / "Scripts_Radiopico");

        // Add python to sys.path
        pybind11::module_ sys = pybind11::module_::import("sys");
        sys.attr("path").attr("insert")(0, scripts_path.string());

        // Check if .venv exists
        std::filesystem::path venv_path = scripts_path / ".venv";
        if (std::filesystem::exists(venv_path))
        {
            // Import sysconfig from .venv to detect python version dynamically
            pybind11::module_ sysconfig = pybind11::module_::import("sysconfig");

            std::string python_version = pybind11::str(sysconfig.attr("get_python_version")());
            std::filesystem::path site_packages = venv_path / "lib" / ("python" + python_version) / "site-packages";

            if (std::filesystem::exists(site_packages))
            {
                sys.attr("path").attr("insert")(0, site_packages.string());
                pybind11::print("Added .venv site-packages:", site_packages.string());
            }
            else
            {
                pybind11::print("Warning: site-packages not found in .venv at ", site_packages.string());
            }
        }
        else
        {
            pybind11::print("No .venv folder detected. Using system Python. At ", venv_path.string());
        }

        // Import main module
        m_displayHandler->messageInfo("Importing Python script...");

        std::string pythonFileName = "ReadBinaryWeeroc";
        script = pybind11::module_::import(pythonFileName.c_str());
        pybind11::print("Imported " + pythonFileName + " successfully.");
    }
    catch (const pybind11::error_already_set &e)
    {
        throw std::runtime_error("Failed to initialize Python environment. What : " + std::string(e.what()));
    }
}

pythonInterface::~pythonInterface()
{
}

bool pythonInterface::readBinaryFile(std::string pathToBinaryFile, double *&tof, double *&energy, size_t &eventSize)
{
    m_displayHandler->messageInfo("Collecting events from binary file : " + pathToBinaryFile);

    if (!std::filesystem::exists(pathToBinaryFile))
    {
        m_displayHandler->messageError("File does not exist : " + pathToBinaryFile);
        return false;
    }

    // Get the data from Python
    pybind11::array_t<double> arrayToT;
    pybind11::array_t<double> arrayToF;

    pybind11::tuple t = callPythonFunction("readBinaryWeerocFileWithPicoCalibrated", pathToBinaryFile);

    arrayToT = t[0].cast<pybind11::array_t<double>>();
    arrayToF = t[1].cast<pybind11::array_t<double>>();
    eventSize = t[2].cast<size_t>();

    m_displayHandler->messageInfo("Collected " + std::to_string(eventSize) + " events from the board.");

    // Allocate memory
    energy = new double[eventSize];
    tof = new double[eventSize];

    // Access Python buffers
    auto bufToT = arrayToT.request();
    auto bufToF = arrayToF.request();

    double *ptrToT = static_cast<double *>(bufToT.ptr);
    double *ptrToF = static_cast<double *>(bufToF.ptr);

    // Deep copy into array
    std::copy(ptrToT, ptrToT + eventSize, energy);
    std::copy(ptrToF, ptrToF + eventSize, tof);

    // buffer python are automatically freed when they go out of scope

    return true;
}
