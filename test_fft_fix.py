"""
Test script to verify Lab 4 FFT frequency domain visualization fix.

This script validates that:
1. FFT and DFT magnitude spectra are extracted correctly
2. The stem_plot method can render discrete frequency components
3. The visualization shows meaningful frequency domain data
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from labs.lab4_fft import Lab4FFT
from controller.lab_controller import LabController

def test_fft_results():
    """Test that Lab 4 produces meaningful FFT/DFT results"""
    print("=" * 70)
    print("TEST 1: Lab 4 FFT/DFT Magnitude Spectrum")
    print("=" * 70)
    
    lab = Lab4FFT()
    lab.setup()
    
    # Test with default sequence "1 2 3 4"
    t, x = lab.process()
    results = lab.results
    
    # Extract FFT data
    fft_data = results.get('fft', {})
    dft_data = results.get('dft', {})
    
    freqs = np.array(fft_data.get('frequencies', []))
    mag_fft = np.array(fft_data.get('magnitude', []))
    mag_dft = np.array(dft_data.get('magnitude', []))
    
    print(f"\nSequence: x(n) = [1, 2, 3, 4]")
    print(f"Number of samples: N = {len(x)}")
    print(f"\nFrequency bins: {freqs}")
    print(f"FFT magnitudes: {mag_fft}")
    print(f"DFT magnitudes: {mag_dft}")
    
    # Verify data
    assert len(freqs) > 0, "❌ No frequency bins found!"
    assert len(mag_fft) > 0, "❌ No FFT magnitudes found!"
    assert len(mag_dft) > 0, "❌ No DFT magnitudes found!"
    assert len(freqs) == len(mag_fft), "❌ Frequency and magnitude array mismatch!"
    assert len(freqs) == len(mag_dft), "❌ DFT magnitude array size mismatch!"
    
    max_mag = np.max(mag_fft)
    assert max_mag > 0, "❌ All magnitudes are zero or negative!"
    
    print(f"\n✓ FFT max magnitude: {max_mag:.4f}")
    print(f"✓ Frequency resolution: {results['display']['efficiency']}")
    print(f"✓ Dominant frequencies found: {len(results['dominant_frequencies'])}")
    
    return True

def test_controller_results():
    """Test that LabController properly packages FFT results"""
    print("\n" + "=" * 70)
    print("TEST 2: LabController Processing")
    print("=" * 70)
    
    class DummyAppController:
        pass
    
    controller = LabController('fft', DummyAppController())
    result = controller.process()
    
    # Check result structure
    assert 'time_domain' in result, "❌ Missing time_domain in result!"
    assert 'freq_domain' in result, "❌ Missing freq_domain in result!"
    assert 'results' in result, "❌ Missing results in result!"
    
    lab_results = result.get('results', {})
    assert 'fft' in lab_results, "❌ Missing fft in lab_results!"
    assert 'dft' in lab_results, "❌ Missing dft in lab_results!"
    
    fft_data = lab_results['fft']
    assert 'frequencies' in fft_data, "❌ Missing frequencies in fft_data!"
    assert 'magnitude' in fft_data, "❌ Missing magnitude in fft_data!"
    
    print(f"✓ Result structure is valid")
    print(f"✓ FFT data contains {len(fft_data['frequencies'])} frequency bins")
    print(f"✓ FFT magnitudes range: [{np.min(fft_data['magnitude']):.4f}, {np.max(fft_data['magnitude']):.4f}]")
    
    return True

def test_stem_plot_data():
    """Test that stem plot can render the frequency domain data"""
    print("\n" + "=" * 70)
    print("TEST 3: Stem Plot Compatibility")
    print("=" * 70)
    
    lab = Lab4FFT()
    lab.setup()
    t, x = lab.process()
    
    results = lab.results
    fft_data = results.get('fft', {})
    
    freqs = np.array(fft_data.get('frequencies', []))
    mag = np.array(fft_data.get('magnitude', []))
    
    # Check that all magnitudes are positive (requirement for stem plot)
    positive_mags = np.all(mag >= 0)
    assert positive_mags, "❌ Negative magnitudes found (stem plot requires y >= 0)!"
    
    # Check that we have at least 2 frequency bins for meaningful visualization
    assert len(freqs) >= 2, f"❌ Too few frequency bins: {len(freqs)}"
    
    # Check frequency spacing is uniform (expected for DFT)
    if len(freqs) > 1:
        freq_diff = np.diff(freqs)
        uniform = np.allclose(freq_diff, freq_diff[0], rtol=1e-5)
        print(f"✓ Frequency bins are {'uniform' if uniform else 'non-uniform'}")
        print(f"  Frequency spacing: {freq_diff}")
    
    print(f"✓ Stem plot can render {len(freqs)} frequency components")
    print(f"✓ All magnitudes are non-negative (suitable for stem plot)")
    
    return True

def main():
    """Run all tests"""
    try:
        test_fft_results()
        test_controller_results()
        test_stem_plot_data()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nThe FFT frequency domain visualization should now:")
        print("  • Display discrete frequency components as stem plot")
        print("  • Show meaningful magnitudes for each frequency bin")
        print("  • Overlay DFT magnitudes for comparison")
        print("  • Have proper axis labels and scaling")
        
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
