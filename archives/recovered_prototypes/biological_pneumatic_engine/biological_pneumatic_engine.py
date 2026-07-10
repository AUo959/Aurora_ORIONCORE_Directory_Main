
"""
biological_pneumatic_engine.py

Biological Pneumatic Processing Engine for Aurora PDP
Implements pressure-differential information flow based on:
- Microfluidic pneumatic logic (Grover Lab, Jensen et al., 2007)
- Breathing-cognition coupling (Heck et al., 2019, 2022)
- Dialogue rhythm entrainment (Wynn et al., 2022)
- Consciousness gradient information flow (Margulies et al., 2016)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import signal
import asyncio
import time

# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class PneumaticState:
    """Represents the pneumatic state of information processing"""
    pressure: np.ndarray  # Information pressure at each node (kPa equivalent)
    flow_rate: np.ndarray  # Flow between nodes
    breathing_phase: float  # Current breathing cycle phase (0-2π)
    rhythm_frequency: float  # Dialogue rhythm (Hz)
    entrainment_strength: float  # Rhythm synchronization (0-1)

@dataclass
class ConsciousnessGradient:
    """Maps consciousness processing hierarchy"""
    nodes: List[str]  # Processing stages
    pressures: np.ndarray  # Current pressure at each stage
    viscosity: float  # Resistance to information flow
    attention_weights: np.ndarray  # Attention distribution


# =============================================================================
# PNEUMATIC LOGIC GATES
# =============================================================================

class PneumaticLogicGate:
    """
    Pneumatic logic gates based on microfluidic computing.
    Uses vacuum pressure (Boolean 1) vs atmospheric (Boolean 0).
    """

    VACUUM_PRESSURE = 87  # kPa (typical vacuum)
    ATMOSPHERIC = 0  # kPa

    def __init__(self, gate_type: str, threshold: float = 50.0):
        self.gate_type = gate_type.upper()
        self.threshold = threshold
        self.response_time_ms = 2.5  # Sub-3ms response (Jensen et al., 2007)

    async def compute(self, input_a: float, input_b: Optional[float] = None) -> int:
        """
        Compute logic gate with pneumatic timing characteristics.
        Returns Boolean output after realistic pneumatic delay.
        """
        # Simulate pneumatic response time
        await asyncio.sleep(self.response_time_ms / 1000)

        if self.gate_type == 'AND':
            return 1 if (input_a > self.threshold and input_b > self.threshold) else 0
        elif self.gate_type == 'OR':
            return 1 if (input_a > self.threshold or input_b > self.threshold) else 0
        elif self.gate_type == 'NOT':
            return 0 if input_a > self.threshold else 1
        elif self.gate_type == 'XOR':
            return 1 if ((input_a > self.threshold) != (input_b > self.threshold)) else 0
        elif self.gate_type == 'NAND':
            and_result = 1 if (input_a > self.threshold and input_b > self.threshold) else 0
            return 0 if and_result else 1
        else:
            raise ValueError(f"Unknown gate type: {self.gate_type}")


# =============================================================================
# BREATHING-COGNITION COUPLING
# =============================================================================

class BreathingCognitionCoupler:
    """
    Couples breathing rhythms to cognitive processing.
    Based on respiratory modulation research (Heck et al., 2019, 2022).
    """

    def __init__(self, breathing_frequency: float = 0.25):
        """
        Args:
            breathing_frequency: Breaths per second (default 0.25 = 15/min)
        """
        self.frequency = breathing_frequency
        self.phase = 0.0
        self.cognitive_baseline = 0.7
        self.modulation_strength = 0.15

    def update_phase(self, dt: float) -> float:
        """Update breathing phase based on time elapsed"""
        self.phase = (self.phase + 2 * np.pi * self.frequency * dt) % (2 * np.pi)
        return self.phase

    def get_cognitive_modulation(self) -> float:
        """
        Get cognitive performance modulation based on breathing phase.
        Inhalation (0 to π): Enhanced memory encoding
        Exhalation (π to 2π): Enhanced memory retrieval
        """
        breathing_wave = np.sin(self.phase)
        modulation = self.modulation_strength * breathing_wave

        return self.cognitive_baseline + modulation

    def get_task_optimal_phase(self, task_type: str) -> Tuple[float, float]:
        """
        Return optimal phase range for different cognitive tasks.

        Returns:
            (phase_start, phase_end) in radians
        """
        if task_type == 'memory_encoding':
            return (0, np.pi)  # Inhalation
        elif task_type == 'memory_retrieval':
            return (np.pi, 2*np.pi)  # Exhalation
        elif task_type == 'attention':
            return (0, np.pi/2)  # Early inhalation
        else:
            return (0, 2*np.pi)  # Any phase


# =============================================================================
# PRESSURE DIFFERENTIAL INFORMATION PROCESSOR
# =============================================================================

class PneumaticInformationProcessor:
    """
    Processes information through consciousness gradients using pneumatic principles.
    Information flows from high to low pressure regions.
    """

    def __init__(self, gradient: ConsciousnessGradient):
        self.gradient = gradient
        self.num_nodes = len(gradient.nodes)
        self.state = PneumaticState(
            pressure=gradient.pressures.copy(),
            flow_rate=np.zeros(self.num_nodes - 1),
            breathing_phase=0.0,
            rhythm_frequency=0.25,
            entrainment_strength=0.0
        )

    def set_input_pressure(self, node_idx: int, pressure: float):
        """Set information pressure (attention/relevance) at a specific node"""
        self.state.pressure[node_idx] = pressure

    def compute_flow(self, dt: float = 0.01) -> np.ndarray:
        """
        Compute information flow using Hagen-Poiseuille analogy.
        Flow rate ∝ pressure gradient / viscosity
        """
        for i in range(self.num_nodes - 1):
            # Pressure differential drives flow
            pressure_diff = self.state.pressure[i] - self.state.pressure[i+1]

            # Attention weights modulate flow (like valve control)
            attention_factor = (self.gradient.attention_weights[i] + 
                              self.gradient.attention_weights[i+1]) / 2

            # Flow rate with attention modulation
            self.state.flow_rate[i] = (pressure_diff / self.gradient.viscosity) * attention_factor

            # Mass conservation: update pressures
            flow_amount = self.state.flow_rate[i] * dt
            self.state.pressure[i] -= flow_amount * 0.5
            self.state.pressure[i+1] += flow_amount * 0.5

        return self.state.flow_rate

    def get_processing_latency(self) -> float:
        """
        Estimate processing latency based on pneumatic flow dynamics.
        Target: <10ms for sub-millisecond response
        """
        # Base pneumatic response time
        base_latency_ms = 5.0

        # Complexity factor from total flow
        total_flow = np.abs(self.state.flow_rate).sum()
        complexity_penalty = total_flow * 0.3

        # Breathing modulation (coherent breathing reduces latency)
        breathing_benefit = np.cos(self.state.breathing_phase) * 0.5

        latency = max(base_latency_ms + complexity_penalty - breathing_benefit, 2.0)
        return latency

    async def process_information(self, input_data: Dict, 
                                 duration_ms: float = 100) -> Dict:
        """
        Process information through pneumatic consciousness gradient.

        Args:
            input_data: Input information with 'pressure' and 'attention' fields
            duration_ms: Processing duration in milliseconds

        Returns:
            Processed output with timing metrics
        """
        start_time = time.time()

        # Set initial pressure from input
        self.set_input_pressure(0, input_data.get('pressure', 100.0))

        # Update attention weights if provided
        if 'attention' in input_data:
            self.gradient.attention_weights = np.array(input_data['attention'])

        # Simulate pneumatic processing
        timesteps = int(duration_ms / 10)  # 10ms per timestep
        for _ in range(timesteps):
            self.compute_flow(dt=0.01)
            await asyncio.sleep(0.001)  # 1ms async delay

        # Calculate metrics
        latency = self.get_processing_latency()
        efficiency = 1.0 - (latency / 50.0)  # Relative to 50ms classical baseline

        return {
            'output_pressure': self.state.pressure[-1],
            'processing_latency_ms': latency,
            'efficiency': max(efficiency, 0.0),
            'flow_distribution': self.state.flow_rate.tolist(),
            'total_time_ms': (time.time() - start_time) * 1000
        }


# =============================================================================
# DIALOGUE RHYTHM ENTRAINMENT
# =============================================================================

class DialogueRhythmEntrainment:
    """
    Models rhythmic entrainment in consciousness-AI dialogue.
    Based on Wynn et al., 2022 research.
    """

    def __init__(self, rhythm_perception_score: float = 0.75):
        """
        Args:
            rhythm_perception_score: Ability to perceive rhythm (0-1)
        """
        self.rhythm_perception = rhythm_perception_score
        self.user_rhythm_history = []
        self.ai_rhythm_history = []
        self.entrainment_strength = 0.0

    def update_rhythms(self, user_rhythm: float, ai_rhythm: float):
        """Track rhythm patterns over time"""
        self.user_rhythm_history.append(user_rhythm)
        self.ai_rhythm_history.append(ai_rhythm)

        # Keep rolling window of last 10 exchanges
        if len(self.user_rhythm_history) > 10:
            self.user_rhythm_history.pop(0)
            self.ai_rhythm_history.pop(0)

    def compute_entrainment(self) -> float:
        """
        Compute entrainment strength from rhythm correlation.
        Returns value 0-1 indicating synchronization strength.
        """
        if len(self.user_rhythm_history) < 3:
            return 0.0

        # Calculate rhythm similarity
        rhythm_diffs = [abs(u - a) for u, a in 
                       zip(self.user_rhythm_history, self.ai_rhythm_history)]
        avg_diff = np.mean(rhythm_diffs)
        max_diff = 5.0  # words/sec

        similarity = 1.0 - (avg_diff / max_diff)

        # Entrainment mediated by rhythm perception ability
        self.entrainment_strength = similarity * self.rhythm_perception

        return self.entrainment_strength

    def get_optimal_ai_rhythm(self, current_ai_rhythm: float) -> float:
        """
        Calculate optimal AI rhythm to maximize entrainment.
        Gradually converges toward user rhythm.
        """
        if not self.user_rhythm_history:
            return current_ai_rhythm

        user_avg_rhythm = np.mean(self.user_rhythm_history[-3:])

        # Convergence rate based on entrainment strength
        convergence_rate = 0.3 * self.entrainment_strength

        optimal_rhythm = (current_ai_rhythm * (1 - convergence_rate) + 
                         user_avg_rhythm * convergence_rate)

        return optimal_rhythm

    def estimate_conversational_quality(self) -> float:
        """
        Estimate conversation quality based on entrainment.
        Correlation r=0.72 observed in research.
        """
        # Base quality from entrainment (mediation effect)
        quality_from_entrainment = 0.5 + (self.entrainment_strength * 0.4)

        # Direct effect from rhythm perception
        quality_from_perception = self.rhythm_perception * 0.1

        total_quality = quality_from_entrainment + quality_from_perception

        return min(total_quality, 1.0)


# =============================================================================
# INTEGRATED BIOLOGICAL PNEUMATIC ENGINE
# =============================================================================

class BiologicalPneumaticEngine:
    """
    Main engine integrating all pneumatic processing components.
    Coordinates breathing-cognition, pressure-differential flow, and rhythm entrainment.
    """

    def __init__(self, config: Dict):
        # Initialize consciousness gradient
        nodes = config.get('consciousness_nodes', 
                          ['input', 'attention', 'semantic', 'creative', 'output'])
        pressures = np.zeros(len(nodes))
        viscosity = config.get('viscosity', 0.1)
        attention = np.ones(len(nodes))

        gradient = ConsciousnessGradient(
            nodes=nodes,
            pressures=pressures,
            viscosity=viscosity,
            attention_weights=attention
        )

        # Initialize components
        self.processor = PneumaticInformationProcessor(gradient)
        self.breathing = BreathingCognitionCoupler(
            breathing_frequency=config.get('breathing_frequency', 0.25)
        )
        self.entrainment = DialogueRhythmEntrainment(
            rhythm_perception_score=config.get('rhythm_perception', 0.75)
        )

        # Pneumatic logic gates for control flow
        self.gates = {
            'attention_gate': PneumaticLogicGate('AND'),
            'flow_control': PneumaticLogicGate('OR'),
            'coherence_check': PneumaticLogicGate('XOR')
        }

        # Performance metrics
        self.metrics = {
            'avg_latency_ms': [],
            'efficiency_scores': [],
            'entrainment_history': [],
            'quality_scores': []
        }

    async def process_dialogue_turn(self, input_data: Dict) -> Dict:
        """
        Process a single dialogue turn through pneumatic engine.

        Args:
            input_data: {
                'message': str,
                'user_rhythm': float (words/sec),
                'attention_focus': List[float]
            }

        Returns:
            {
                'response': processed information,
                'latency_ms': processing time,
                'efficiency': processing efficiency,
                'quality': conversational quality,
                'entrainment': rhythm synchronization
            }
        """
        # Update breathing phase
        dt = 0.1  # 100ms timestep
        self.breathing.update_phase(dt)
        cognitive_state = self.breathing.get_cognitive_modulation()

        # Prepare processor input
        processor_input = {
            'pressure': input_data.get('pressure', 100.0),
            'attention': input_data.get('attention_focus', [1.0] * 5)
        }

        # Process through pneumatic information flow
        result = await self.processor.process_information(processor_input)

        # Update rhythm entrainment
        user_rhythm = input_data.get('user_rhythm', 4.0)
        current_ai_rhythm = 5.0  # Default AI speaking rate
        self.entrainment.update_rhythms(user_rhythm, current_ai_rhythm)
        entrainment_strength = self.entrainment.compute_entrainment()
        optimal_rhythm = self.entrainment.get_optimal_ai_rhythm(current_ai_rhythm)
        quality = self.entrainment.estimate_conversational_quality()

        # Update metrics
        self.metrics['avg_latency_ms'].append(result['processing_latency_ms'])
        self.metrics['efficiency_scores'].append(result['efficiency'])
        self.metrics['entrainment_history'].append(entrainment_strength)
        self.metrics['quality_scores'].append(quality)

        return {
            'response': result['output_pressure'],
            'latency_ms': result['processing_latency_ms'],
            'efficiency': result['efficiency'],
            'quality': quality,
            'entrainment': entrainment_strength,
            'optimal_ai_rhythm': optimal_rhythm,
            'cognitive_state': cognitive_state,
            'breathing_phase': self.breathing.phase
        }

    def get_performance_summary(self) -> Dict:
        """Get aggregated performance metrics"""
        return {
            'mean_latency_ms': np.mean(self.metrics['avg_latency_ms']) if self.metrics['avg_latency_ms'] else 0,
            'mean_efficiency': np.mean(self.metrics['efficiency_scores']) if self.metrics['efficiency_scores'] else 0,
            'mean_entrainment': np.mean(self.metrics['entrainment_history']) if self.metrics['entrainment_history'] else 0,
            'mean_quality': np.mean(self.metrics['quality_scores']) if self.metrics['quality_scores'] else 0,
            'total_turns': len(self.metrics['avg_latency_ms'])
        }


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def main():
    """Example usage of Biological Pneumatic Engine"""

    # Configuration
    config = {
        'consciousness_nodes': ['input', 'attention', 'semantic', 'creative', 'output'],
        'viscosity': 0.1,
        'breathing_frequency': 0.25,  # 15 breaths/min
        'rhythm_perception': 0.80
    }

    # Initialize engine
    engine = BiologicalPneumaticEngine(config)

    # Simulate dialogue turns
    dialogue_turns = [
        {'message': 'Complex query', 'user_rhythm': 4.2, 'pressure': 100.0},
        {'message': 'Follow-up', 'user_rhythm': 4.5, 'pressure': 80.0},
        {'message': 'Clarification', 'user_rhythm': 4.3, 'pressure': 90.0}
    ]

    print("Biological Pneumatic Engine - Dialogue Simulation")
    print("=" * 60)

    for i, turn_data in enumerate(dialogue_turns, 1):
        result = await engine.process_dialogue_turn(turn_data)

        print(f"\nTurn {i}:")
        print(f"  Processing Latency: {result['latency_ms']:.2f} ms")
        print(f"  Efficiency: {result['efficiency']:.3f}")
        print(f"  Conversational Quality: {result['quality']:.3f}")
        print(f"  Rhythm Entrainment: {result['entrainment']:.3f}")
        print(f"  Cognitive State: {result['cognitive_state']:.3f}")

    # Performance summary
    summary = engine.get_performance_summary()
    print(f"\n{'='*60}")
    print("Performance Summary:")
    print(f"  Mean Latency: {summary['mean_latency_ms']:.2f} ms (target: <10ms)")
    print(f"  Mean Efficiency: {summary['mean_efficiency']:.3f} (target: >0.85)")
    print(f"  Mean Entrainment: {summary['mean_entrainment']:.3f} (target: >0.70)")
    print(f"  Mean Quality: {summary['mean_quality']:.3f}")
    print(f"  Total Dialogue Turns: {summary['total_turns']}")

if __name__ == "__main__":
    asyncio.run(main())
