import os
import numpy as np
import scipy.signal as signal
import plotly.graph_objects as gr
from plotly.subplots import make_subplots

# Parameters
f_nom = 2.0e6
f_mod = 50.0e3
delta_f = 200.0e3
duration = 40.0e-6
t_edge = 0.2e-9
fs_fft = 500e6

def hershey_kiss_profile(theta, d=0.8):
    psi = np.mod(theta, 2 * np.pi)
    val = np.zeros_like(psi)
    
    # Segment 1: [0, pi/2]
    idx1 = (psi >= 0) & (psi < np.pi/2)
    z1 = psi[idx1] / (np.pi/2)
    val[idx1] = (1 - d/2) * z1 + (d/2) * (z1 ** 2)
    
    # Segment 2: [pi/2, pi]
    idx2 = (psi >= np.pi/2) & (psi < np.pi)
    z2 = (np.pi - psi[idx2]) / (np.pi/2)
    val[idx2] = (1 - d/2) * z2 + (d/2) * (z2 ** 2)
    
    # Segment 3: [pi, 3*pi/2]
    idx3 = (psi >= np.pi) & (psi < 1.5 * np.pi)
    z3 = (psi[idx3] - np.pi) / (np.pi/2)
    val[idx3] = -((1 - d/2) * z3 + (d/2) * (z3 ** 2))
    
    # Segment 4: [1.5 * np.pi, 2*pi]
    idx4 = (psi >= 1.5 * np.pi) & (psi <= 2 * np.pi)
    z4 = (2 * np.pi - psi[idx4]) / (np.pi/2)
    val[idx4] = -((1 - d/2) * z4 + (d/2) * (z4 ** 2))
    
    return val

def get_modulation_profile(t, f_nom, f_mod, delta_f, profile_type='triangular', steps=None):
    if profile_type == 'sinusoidal':
        val = np.sin(2 * np.pi * f_mod * t)
    elif profile_type == 'triangular':
        val = signal.sawtooth(2 * np.pi * f_mod * t + np.pi/2, width=0.5)
    elif profile_type == 'hershey_kiss':
        val = hershey_kiss_profile(2 * np.pi * f_mod * t, d=0.8)
    elif profile_type == 'random':
        np.random.seed(42)
        val = np.zeros_like(t)
        for i in range(1, 6):
            phase = np.random.rand() * 2 * np.pi
            val += np.sin(2 * np.pi * (f_mod * i / 2.0) * t + phase) / i
        val = val / np.max(np.abs(val)) if np.max(np.abs(val)) > 0 else val
    else:
        val = np.zeros_like(t)
        
    if steps is not None and steps > 0:
        bin_edges = np.linspace(-1, 1, steps)
        idx = np.abs(val[:, None] - bin_edges).argmin(axis=1)
        val = bin_edges[idx]
        
    return f_nom + delta_f * val

def generate_sscg_clock(f_nom, f_mod, delta_f, profile_type='triangular', steps=None, duration=40e-6, t_edge=0.2e-9):
    t_events, v_events = [], []
    t_midpoints, f_profile = [], []
    t_current = 0.0
    
    while t_current < duration:
        freq = get_modulation_profile(np.array([t_current]), f_nom, f_mod, delta_f, profile_type, steps)[0]
        T_cycle = 1.0 / freq
        T_high = 0.5 * T_cycle
        
        t_midpoints.append(t_current)
        f_profile.append(freq)
        
        t_events.extend([t_current, t_current + t_edge, t_current + T_high, t_current + T_high + t_edge])
        v_events.extend([0.0, 1.0, 1.0, 0.0])
        t_current += T_cycle
        
    return np.array(t_events), np.array(v_events), np.array(t_midpoints), np.array(f_profile)

def measure_clock_parameters(t_seq, v_seq, threshold=0.5):
    crossings, crossing_types = [], []
    for i in range(len(t_seq) - 1):
        v1, v2 = v_seq[i], v_seq[i+1]
        t1, t2 = t_seq[i], t_seq[i+1]
        if (v1 <= threshold < v2) or (v1 >= threshold > v2):
            t_cross = t1 + (threshold - v1) * (t2 - t1) / (v2 - v1)
            crossings.append(t_cross)
            crossing_types.append('rise' if v2 > v1 else 'fall')
            
    crossings = np.array(crossings)
    crossing_types = np.array(crossing_types)
    rise_indices = np.where(crossing_types == 'rise')[0]
    
    measured_times, measured_freqs, measured_duties = [], [], []
    for idx in range(len(rise_indices) - 1):
        r1_idx = rise_indices[idx]
        r2_idx = rise_indices[idx + 1]
        t_rise1, t_rise2 = crossings[r1_idx], crossings[r2_idx]
        fall_idx = r1_idx + 1
        if fall_idx < len(crossings) and crossing_types[fall_idx] == 'fall' and crossings[fall_idx] < t_rise2:
            t_fall = crossings[fall_idx]
            period = t_rise2 - t_rise1
            high_duration = t_fall - t_rise1
            measured_times.append(t_rise2)
            measured_freqs.append(1.0 / period)
            measured_duties.append((high_duration / period) * 100.0)
            
    return np.array(measured_times), np.array(measured_freqs), np.array(measured_duties)

def compute_spectrum(t_seq, v_seq, duration, fs=500e6):
    num_samples = int(duration * fs)
    t_uniform = np.linspace(0, duration, num_samples, endpoint=False)
    v_uniform = np.interp(t_uniform, t_seq, v_seq)
    fft_vals = np.fft.rfft(v_uniform - np.mean(v_uniform))
    freq_bins = np.fft.rfftfreq(num_samples, 1.0 / fs)
    magnitude = 20 * np.log10(np.abs(fft_vals) / num_samples + 1e-10)
    return freq_bins, magnitude

def save_interactive_plot(profile_type, steps=None):
    print(f"Generating and saving report for {profile_type.replace('_', ' ').upper()}...")
    t_base, v_base, _, _ = generate_sscg_clock(f_nom, f_mod, 0, 'fixed', None, duration, t_edge)
    freq_bins_base, mag_base = compute_spectrum(t_base, v_base, duration, fs=fs_fft)
    
    t_seq, v_seq, t_midpoints, f_profile = generate_sscg_clock(f_nom, f_mod, delta_f, profile_type, steps, duration, t_edge)
    t_meas, f_meas, d_meas = measure_clock_parameters(t_seq, v_seq)
    freq_bins, mag = compute_spectrum(t_seq, v_seq, duration, fs=fs_fft)
    
    peak_base = np.max(mag_base[(freq_bins_base > 0.5e6) & (freq_bins_base < 10e6)])
    peak_mod = np.max(mag[(freq_bins > 0.5e6) & (freq_bins < 10e6)])
    attenuation = peak_base - peak_mod
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.08,
        subplot_titles=(
            f"Digital Clock Waveform ({profile_type.replace('_', ' ').title()} modulation)",
            f"SSCG Frequency Profile (Nominal: {f_nom*1e-6:.1f}MHz, Spread: ±{delta_f*1e-3:.1f}kHz)",
            f"Measured Duty Cycle vs Time (Avg: {np.mean(d_meas):.2f}%)",
            f"EMI Power Spectrum (FFT) | Peak EMI Reduction: {attenuation:.2f} dB"
        )
    )
    
    fig.add_trace(gr.Scatter(x=t_seq*1e6, y=v_seq, mode='lines', name='Clock Waveform', line=dict(color='#636EFA', width=1.5)), row=1, col=1)
    fig.add_trace(gr.Scatter(x=t_midpoints*1e6, y=f_profile*1e-6, mode='lines', name='Ideal Profile', line=dict(color='#EF553B', width=2.5, dash='dash')), row=2, col=1)
    fig.add_trace(gr.Scatter(x=t_meas*1e6, y=f_meas*1e-6, mode='markers+lines', name='Measured Freq', marker=dict(color='#00CC96', size=5)), row=2, col=1)
    fig.add_trace(gr.Scatter(x=t_meas*1e6, y=d_meas, mode='markers+lines', name='Measured Duty', marker=dict(color='#AB63FA', size=5)), row=3, col=1)
    fig.add_trace(gr.Scatter(x=freq_bins_base*1e-6, y=mag_base, mode='lines', name='Unmodulated Base', line=dict(color='#BDC3C7', width=1)), row=4, col=1)
    fig.add_trace(gr.Scatter(x=freq_bins*1e-6, y=mag, mode='lines', name='SSCG Modulated', line=dict(color='#FF6692', width=1.5)), row=4, col=1)
    
    fig.update_xaxes(title_text="Time (μs)", row=1, col=1)
    fig.update_xaxes(title_text="Time (μs)", row=2, col=1)
    fig.update_xaxes(title_text="Time (μs)", row=3, col=1)
    fig.update_xaxes(title_text="Frequency (MHz)", range=[0, 10], row=4, col=1)
    
    fig.update_yaxes(title_text="Clock Amp", range=[-0.2, 1.2], row=1, col=1)
    fig.update_yaxes(title_text="Freq (MHz)", row=2, col=1)
    fig.update_yaxes(title_text="Duty (%)", range=[45, 55], row=3, col=1)
    fig.update_yaxes(title_text="Magnitude (dB)", row=4, col=1)
    
    fig.update_layout(height=950, template='plotly_white', title=dict(text=f"SSCG Modulation Analysis: {profile_type.replace('_', ' ').upper()}", x=0.5))
    
    filename = f"sscg_{profile_type}_report.html"
    fig.write_html(filename)
    print(f"Saved interactive report as '{filename}'")

if __name__ == '__main__':
    save_interactive_plot('triangular', steps=8)
    save_interactive_plot('sinusoidal')
    save_interactive_plot('hershey_kiss')
    save_interactive_plot('random')
    print("All report files generated successfully!")
