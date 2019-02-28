#!/usr/bin/env python3
# add logger, to allow logging to Labber's instrument log
import logging
import numpy as np
import gates
import sequence

log = logging.getLogger('LabberDriver')


class Rabi(sequence.Sequence):
    """Sequence for driving Rabi oscillations in multiple qubits."""

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # just add pi-pulses for the number of available qubits
        self.add_gate_to_all(gates.Xp, align='right')


class CPMG(sequence.Sequence):
    """Sequence for multi-qubit Ramsey/Echo/CMPG experiments."""

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # get parameters
        n_pulse = int(config['# of pi pulses'])
        pi_to_q = config['Add pi pulses to Q']
        seqduration = config['Sequence duration']
        edge_to_edge = config['Edge-to-edge pulses']
        pulse_shape = config['Pulse type']
        uniform = config['Uniform pulse shape']

        if uniform:
            width = config['Width']
            plateau = config['Plateau']
        else:
            widthlist = []
            plateaulist = []
            for i in range(1, 10):
                widthlist.append(config['Width #' + str(i)])
                plateaulist.append(config['Plateau #' + str(i)])
            width = max(widthlist)
            plateau = max(plateaulist)

        # defines the actual width of a pulse depending on the pulse shape
        if pulse_shape == 'Gaussian':
            truncation_val = config['Truncation range']
            width_e2e = truncation_val*width + plateau
        elif pulse_shape == 'Ramp':
            width_e2e = 2 * width + plateau
        else:
            width_e2e = width + plateau

        # select type of refocusing pi pulse
        gate_pi = gates.Yp if pi_to_q else gates.Xp

        # redefines the sequence duration if edge-to-edge
        if edge_to_edge:
            duration = seqduration + width_e2e
            T1duration = duration
        else:
            duration = seqduration
            T1duration = duration + width_e2e/2

        # generates the sequence
        if n_pulse < 0:
            self.add_gate_to_all(gates.IdentityGate(width=0), t0=0)
            self.add_gate_to_all(gate_pi)
            self.add_gate_to_all(gates.IdentityGate(width=0), t0=T1duration)
        else:
            self.add_gate_to_all(gates.IdentityGate(width=0), t0=0)
            self.add_gate_to_all(gates.X2p)
            for i in range(n_pulse):
                self.add_gate_to_all(
                    gates.IdentityGate(width=0), t0=duration/(n_pulse+1)*(i+1))
                self.add_gate_to_all(
                    gate_pi)
            self.add_gate_to_all(gates.IdentityGate(width=0), t0=duration)
            self.add_gate_to_all(gates.X2p)


class PulseTrain(sequence.Sequence):
    """Sequence for multi-qubit pulse trains, for pulse calibrations."""

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""
        # get parameters
        n_pulse = int(config['# of pulses'])
        alternate = config['Alternate pulse direction']

        if n_pulse == 0:
            self.add_gate_to_all(gates.I)
        for n in range(n_pulse):
            pulse_type = config['Pulse']
            # check if alternate pulses
            if alternate and (n % 2) == 1:
                pulse_type = pulse_type.replace('p', 'm')
                gate = getattr(gates, pulse_type)
            else:
                gate = getattr(gates, pulse_type)
            self.add_gate_to_all(gate)


class SpinLocking(sequence.Sequence):
    """ Sequence for spin-locking experiment.

    """

    def generate_sequence(self, config):
        """Generate sequence by adding gates/pulses to waveforms."""

        pulse_amps = []
        for ii in range(9):
            pulse_amps.append(
                float(config['Drive pulse amplitude #' + str(ii + 1)]))
        pulse_duration = float(config['Drive pulse duration'])
        pulse_phase = float(config['Drive pulse phase']) / 180.0 * np.pi
        pulse_sequence = config['Pulse sequence']

        if pulse_sequence == 'SL-3':
            self.add_gate_to_all(gates.Y2p)
        if pulse_sequence == 'SL-5a':
            self.add_gate_to_all(gates.Y2m)
        if pulse_sequence == 'SL-5b':
            self.add_gate_to_all(gates.Y2p)

        if pulse_sequence != 'SL-3':
            self.add_gate_to_all(gates.Xp)

        rabi_gates = []
        for ii in range(self.n_qubit):
            rabi_gates.append(
                gates.RabiGate(pulse_amps[ii], pulse_duration, pulse_phase))
        self.add_gate(list(range(self.n_qubit)), rabi_gates)
        if pulse_sequence != 'SL-3':
            self.add_gate_to_all(gates.Xp)

        if pulse_sequence == 'SL-3':
            self.add_gate_to_all(gates.Y2p)
        if pulse_sequence == 'SL-5a':
            self.add_gate_to_all(gates.Y2m)
        if pulse_sequence == 'SL-5b':
            self.add_gate_to_all(gates.Y2p)

        return


if __name__ == '__main__':
    pass
