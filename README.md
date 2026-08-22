# Digital-Signal-Processing-Application
# DSPulse Studio

> **An interactive Digital Signal Processing application built with Python and PySide6 for learning, analyzing, and visualizing digital signals.**

DSPulse Studio is a desktop-based **Digital Signal Processing (DSP)** application designed to provide an interactive environment for studying fundamental DSP concepts through signal generation, mathematical analysis, visualization, and laboratory exercises.

The application combines a graphical user interface with signal-processing algorithms to make concepts such as **sampling, aliasing, quantization, Fourier analysis, windowing, and digital filtering** easier to explore and understand.

This project was developed as an academic and engineering project for studying and applying Digital Signal Processing concepts in a practical software environment.

---

## ✨ Features

### 📈 Signal Generation

Generate and visualize common digital signals using configurable parameters such as:

* Signal frequency
* Sampling frequency
* Amplitude
* Phase
* Number of samples

### 🔬 Signal Analysis

Analyze signals in both the **time domain** and **frequency domain**.

* Time-domain waveform visualization
* Frequency-domain analysis
* FFT-based spectral analysis
* Magnitude spectrum
* Frequency component identification

### ⚡ Sampling & Aliasing

Explore the relationship between signal frequency and sampling frequency.

The application can be used to demonstrate:

* Sampling theorem
* Nyquist frequency
* Nyquist rate
* Undersampling
* Oversampling
* Aliasing detection

### 🪟 Windowing

Experiment with common windowing techniques used in spectral analysis:

* Rectangular
* Hamming
* Hann
* Blackman

Window functions can be compared to observe their effects on spectral leakage and frequency analysis.

### 🎚️ Digital Filtering

The application provides tools for experimenting with digital signal filtering, including filter-based signal processing and visualization of filtered results.

### 🧮 Quantization

Explore the effects of analog-to-digital conversion parameters such as:

* ADC resolution
* Number of bits
* Quantization levels
* Quantization error
* Signal-to-noise ratio (SNR)

### 🧪 DSP Laboratory Modules

The project includes dedicated laboratory modules for practicing different DSP concepts.

The laboratory structure allows individual experiments to be developed and tested independently.

---

## 🖥️ Application Architecture

DSPulse Studio follows a modular architecture to keep the user interface, DSP algorithms, laboratory activities, and application control separated.

```text
Digital-Signal-Processing-Application/
│
├── controller/          # Application control and interaction logic
├── core/                # Core DSP algorithms and signal processing
├── labs/                # DSP laboratory modules
├── ui/                  # PySide6 user-interface components
├── icons/               # Application icons and graphical resources
│
├── filtered_audio/      # Generated/processed audio files
├── filtered_images/     # Generated/processed image outputs
│
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
│
├── test_fft_fix.py      # FFT testing
├── test_lab4_plot.py    # Laboratory plotting tests
│
├── TODO.md              # Development roadmap
├── LICENSE              # Project license
└── README.md            # Project documentation
```

---

## 🛠️ Technology Stack

| Technology       | Purpose                                     |
| ---------------- | ------------------------------------------- |
| **Python**       | Core application development                |
| **PySide6**      | Graphical user interface                    |
| **NumPy**        | Numerical computation and signal processing |
| **SciPy**        | Scientific and DSP algorithms               |
| **Matplotlib**   | Signal and spectrum visualization           |
| **PyInstaller**  | Application packaging                       |
| **Git / GitHub** | Version control and project management      |

---

## 🚀 Getting Started

### Requirements

Make sure you have:

* Python 3.10 or newer
* Git
* pip

### 1. Clone the repository

```bash
git clone https://github.com/Seanscript-dev/Digital-Signal-Processing-Application.git
```

### 2. Enter the project directory

```bash
cd Digital-Signal-Processing-Application
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python main.py
```

---

## 📚 DSP Concepts Covered

DSPulse Studio is designed around practical exploration of fundamental DSP concepts, including:

* Continuous-time and discrete-time signals
* Signal generation
* Sampling
* Nyquist theorem
* Aliasing
* Quantization
* ADC resolution
* Signal-to-noise ratio
* Discrete Fourier Transform (DFT)
* Fast Fourier Transform (FFT)
* Frequency-domain analysis
* Spectral leakage
* Windowing
* Digital filtering
* Signal visualization

---

## 🧪 Testing

The project includes test scripts for validating important parts of the application.

Run a test using:

```bash
python test_fft_fix.py
```

or:

```bash
python test_lab4_plot.py
```

Additional tests can be added as the application continues to evolve.

---

## 🎯 Project Goals

The primary goals of DSPulse Studio are to:

1. Provide an interactive environment for learning DSP.
2. Visualize mathematical DSP concepts in an intuitive way.
3. Allow students to experiment with signal-processing parameters.
4. Demonstrate the relationship between mathematical theory and practical implementation.
5. Provide a modular foundation for additional DSP laboratory activities.
6. Apply software engineering principles to an engineering-focused application.

---

## 🔮 Future Improvements

Planned improvements may include:

* [ ] Additional DSP laboratory modules
* [ ] Real-time audio signal processing
* [ ] More digital filter types
* [ ] FIR and IIR filter design tools
* [ ] Z-transform visualization
* [ ] DFT vs. FFT comparison
* [ ] Convolution visualization
* [ ] Interactive spectrogram
* [ ] Audio recording and playback
* [ ] Improved automated testing
* [ ] Application installer/release builds
* [ ] User documentation and tutorials

---

## 👨‍💻 Author

**Sean Darrell Tungcol**

Computer Engineering Student
Philippines

GitHub: **[Seanscript-dev](https://github.com/Seanscript-dev)**

---

## 📄 License

This project is licensed under the **Apache License 2.0**.

See the [`LICENSE`](LICENSE) file for more information.

---

## ⭐ Acknowledgment

DSPulse Studio was developed as an academic and engineering project to apply concepts learned in **Digital Signal Processing** through practical software development.

The project demonstrates how mathematical DSP concepts can be implemented as interactive software tools for experimentation, visualization, and learning.
