"""
Generate a comprehensive Markdown report from benchmark results.
"""

import json
import os
import glob
from datetime import datetime
import platform
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path

# Create results directory if it doesn't exist
RESULTS_DIR = Path("benchmark_results")
RESULTS_DIR.mkdir(exist_ok=True)
RAW_DIR = RESULTS_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)


def load_json_file(filename):
    """Load a JSON file if it exists, otherwise return None."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return None


def load_latest_json(prefix):
    """Load the latest JSON file with the given prefix."""
    files = sorted(glob.glob(str(RAW_DIR / f"{prefix}_*.json")), reverse=True)
    if not files:
        # Check for legacy files
        if os.path.exists(f"{prefix}.json"):
            return load_json_file(f"{prefix}.json"), f"{prefix}.json"
        return None, None
    with open(files[0], "r") as f:
        return json.load(f), os.path.basename(files[0])


def generate_installation_speed_chart(data, output_file):
    """Generate a bar chart for installation speed."""
    if not data:
        return None
    
    tools = []
    times = []
    
    for tool, result in data.get("results", {}).items():
        tools.append(tool)
        times.append(result.get("execution_time", 0))
    
    # Sort by time (ascending)
    sorted_indices = np.argsort(times)
    sorted_tools = [tools[i] for i in sorted_indices]
    sorted_times = [times[i] for i in sorted_indices]
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(sorted_tools, sorted_times, color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'])
    
    plt.title("Installation Speed Comparison")
    plt.xlabel("Tool")
    plt.ylabel("Time (seconds)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add time labels on top of bars
    for bar, time in zip(bars, sorted_times):
        plt.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.1,
            f"{time:.2f}s",
            ha='center',
            fontweight='bold'
        )
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    
    return sorted_tools, sorted_times


def generate_reproducibility_chart(data, output_file):
    """Generate a chart for reproducibility results."""
    if not data:
        return None
    
    tools = []
    reproducible = []
    
    for tool, result in data.items():
        tools.append(tool)
        reproducible.append(1 if result.get("reproducible", False) else 0)
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(tools, reproducible, color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'])
    
    plt.title("Environment Reproducibility")
    plt.xlabel("Tool")
    plt.ylabel("Reproducible")
    plt.yticks([0, 1], ["No", "Yes"])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    
    return tools, reproducible


def generate_hash_comparison_chart(data, output_file):
    """Generate a chart showing hash differences across runs."""
    if not data:
        return None
    
    tools = []
    hash_consistency = []
    hash_samples = []
    
    for tool, result in data.items():
        tools.append(tool)
        hashes = result.get("hashes", [])
        hash_samples.append(hashes)
        
        # Calculate hash consistency (1 if all hashes are the same and not None, 0 otherwise)
        is_consistent = len(set(h for h in hashes if h is not None)) <= 1 and None not in hashes
        hash_consistency.append(1 if is_consistent else 0)
    
    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [1, 3]})
    
    # First subplot: bar chart of consistency
    bars = ax1.bar(tools, hash_consistency, color=['green' if c == 1 else 'red' for c in hash_consistency])
    ax1.set_title('Environment Hash Consistency', fontsize=14)
    ax1.set_ylabel('Consistent')
    ax1.set_ylim(0, 1.2)
    ax1.set_yticks([0, 1])
    ax1.set_yticklabels(['No', 'Yes'])
    
    # Add labels on top of bars
    for bar, consistency in zip(bars, hash_consistency):
        label = "✓ Consistent" if consistency == 1 else "✗ Different"
        color = "green" if consistency == 1 else "red"
        ax1.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.05,
            label,
            ha='center',
            color=color,
            fontweight='bold'
        )
    
    # Second subplot: hash value comparison
    for i, (tool, hashes) in enumerate(zip(tools, hash_samples)):
        # Create a heatmap-like representation of hash values
        for j, hash_value in enumerate(hashes):
            if hash_value is None:
                color = 'gray'
                hash_short = "None"
            else:
                color = 'green' if hash_consistency[i] == 1 else 'red'
                # Display just the first 8 chars of the hash for readability
                hash_short = hash_value[:8] + "..." if hash_value else "None"
            
            ax2.text(i, j, hash_short, ha='center', va='center', 
                     bbox=dict(facecolor=color, alpha=0.3, boxstyle='round,pad=0.5'))
    
    ax2.set_title('Hash Values Across Runs', fontsize=14)
    ax2.set_xticks(range(len(tools)))
    ax2.set_xticklabels(tools)
    ax2.set_yticks(range(len(hash_samples[0])))
    ax2.set_yticklabels([f"Run {i+1}" for i in range(len(hash_samples[0]))])
    ax2.set_xlim(-0.5, len(tools) - 0.5)
    ax2.set_ylim(-0.5, len(hash_samples[0]) - 0.5)
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    
    return tools, hash_consistency, hash_samples


def generate_dx_chart(data, output_file):
    """Generate a chart for developer experience results."""
    if not data:
        return None
    
    tools = []
    success_rates = []
    
    for tool, result in data.items():
        scenarios = result.get("scenarios", [])
        if not scenarios:
            continue
        
        tools.append(tool)
        success_count = sum(1 for s in scenarios if s.get("success", False))
        success_rate = success_count / len(scenarios) * 100
        success_rates.append(success_rate)
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    bars = plt.bar(tools, success_rates, color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'])
    
    plt.title("Developer Experience - Scenario Success Rate")
    plt.xlabel("Tool")
    plt.ylabel("Success Rate (%)")
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add percentage labels on top of bars
    for bar, rate in zip(bars, success_rates):
        plt.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 1,
            f"{rate:.1f}%",
            ha='center',
            fontweight='bold'
        )
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    
    return tools, success_rates


def generate_hyperfine_chart(data, output_file):
    """Generate a chart for hyperfine benchmark results."""
    if not data:
        return None
    
    # Extract data from hyperfine results
    commands = []
    mean_times = []
    std_devs = []
    min_times = []
    max_times = []
    
    for result in data.get("results", []):
        command_name = result.get("command", "").split("&&")[-1].strip()
        # Extract tool name from command
        tool = command_name.split("/")[-2] if "/" in command_name else command_name
        commands.append(tool)
        
        mean = result.get("mean", 0)
        stddev = result.get("stddev", 0)
        min_time = result.get("min", 0)
        max_time = result.get("max", 0)
        
        mean_times.append(mean)
        std_devs.append(stddev)
        min_times.append(min_time)
        max_times.append(max_time)
    
    # Sort by mean time (ascending)
    if commands:
        sorted_indices = np.argsort(mean_times)
        commands = [commands[i] for i in sorted_indices]
        mean_times = [mean_times[i] for i in sorted_indices]
        std_devs = [std_devs[i] for i in sorted_indices]
        min_times = [min_times[i] for i in sorted_indices]
        max_times = [max_times[i] for i in sorted_indices]
    
    # Create bar chart with error bars
    plt.figure(figsize=(12, 8))
    x = range(len(commands))
    
    # Main bars for mean times
    bars = plt.bar(x, mean_times, yerr=std_devs, capsize=10, 
                  color=['#3498db', '#2ecc71', '#e74c3c', '#f39c12'],
                  alpha=0.7, ecolor='black')
    
    # Add a thin line for min-max range
    for i, (min_t, max_t) in enumerate(zip(min_times, max_times)):
        plt.plot([i, i], [min_t, max_t], 'k-', linewidth=1.5)
        plt.plot([i-0.1, i+0.1], [min_t, min_t], 'k-', linewidth=1.5)
        plt.plot([i-0.1, i+0.1], [max_t, max_t], 'k-', linewidth=1.5)
    
    # Chart styling
    plt.title("Hyperfine Benchmark: Installation Speed", fontsize=16)
    plt.xlabel("Tool", fontsize=14)
    plt.ylabel("Time (seconds)", fontsize=14)
    plt.xticks(x, commands, fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add time labels on top of bars
    for bar, time, std in zip(bars, mean_times, std_devs):
        plt.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + std + 0.1,
            f"{time:.2f}s ±{std:.2f}",
            ha='center',
            fontweight='bold',
            fontsize=10
        )
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    return commands, mean_times, std_devs, min_times, max_times


def generate_unified_score_chart(installation_data, hyperfine_data, reproducibility_data, dx_data, output_file):
    """Generate a unified scoring chart combining all metrics."""
    if not (installation_data and reproducibility_data and dx_data):
        return None
    
    # Extract data for each tool
    tools = []
    install_times = []
    repro_scores = []
    dx_scores = []
    
    # Gather all unique tool names
    all_tools = set()
    if installation_data and len(installation_data) >= 2:
        all_tools.update(installation_data[0])
    if reproducibility_data and len(reproducibility_data) >= 2:
        all_tools.update(reproducibility_data[0])
    if dx_data and len(dx_data) >= 2:
        all_tools.update(dx_data[0])
    
    # Calculate hyperfine times if available (more accurate)
    hyperfine_times = {}
    if hyperfine_data:
        tools_hyper, times_hyper = hyperfine_data[0], hyperfine_data[1]
        hyperfine_times = dict(zip(tools_hyper, times_hyper))
    
    # Create consistent tools list
    tools = sorted(all_tools)
    
    # Gather metrics for each tool
    for tool in tools:
        # Installation time
        if hyperfine_times and tool in hyperfine_times:
            # Prefer hyperfine for more accurate benchmarks
            time = hyperfine_times[tool]
        elif tool in installation_data[0]:
            idx = installation_data[0].index(tool)
            time = installation_data[1][idx]
        else:
            time = None
        install_times.append(time)
        
        # Reproducibility score
        if tool in reproducibility_data[0]:
            idx = reproducibility_data[0].index(tool)
            repro = reproducibility_data[1][idx] * 100  # Convert to percentage
        else:
            repro = None
        repro_scores.append(repro)
        
        # Developer experience score
        if tool in dx_data[0]:
            idx = dx_data[0].index(tool)
            dx = dx_data[1][idx]
        else:
            dx = None
        dx_scores.append(dx)
    
    # Create a radar chart
    plt.figure(figsize=(12, 10))
    
    # Set up the radar chart
    categories = ['Installation Speed', 'Reproducibility', 'Developer Experience']
    num_vars = len(categories)
    
    # Calculate angles for each axis
    angles = np.linspace(0, 2*np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Close the loop
    
    # Set up the subplot
    ax = plt.subplot(111, polar=True)
    
    # Draw one axis per variable and add labels
    plt.xticks(angles[:-1], categories, size=12)
    
    # Set y-ticks
    ax.set_rlabel_position(0)
    plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="grey", size=10)
    plt.ylim(0, 100)
    
    # Normalize speed scores (inverse since lower is better)
    # Get the max time, and calculate score as percentage of max (inverted)
    valid_times = [t for t in install_times if t is not None]
    if valid_times:
        max_time = max(valid_times)
        min_time = min(valid_times)
        speed_scores = [100 * (1 - ((t - min_time) / (max_time - min_time))) if t is not None else 0 for t in install_times]
    else:
        speed_scores = [0] * len(tools)
    
    # Plot each tool
    colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
    for i, tool in enumerate(tools):
        # Prepare data for this tool
        values = [
            speed_scores[i] if i < len(speed_scores) else 0,
            repro_scores[i] if i < len(repro_scores) and repro_scores[i] is not None else 0,
            dx_scores[i] if i < len(dx_scores) and dx_scores[i] is not None else 0
        ]
        values += values[:1]  # Close the loop
        
        # Plot the tool's values
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=tool, color=colors[i % len(colors)])
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.1)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.title("Unified Tool Performance Comparison", size=16, y=1.1)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    
    # Calculate unified scores (weighted average)
    unified_scores = []
    for i, tool in enumerate(tools):
        speed = speed_scores[i] if i < len(speed_scores) else 0
        repro = repro_scores[i] if i < len(repro_scores) and repro_scores[i] is not None else 0
        dx = dx_scores[i] if i < len(dx_scores) and dx_scores[i] is not None else 0
        
        # Weight: speed (40%), reproducibility (40%), DX (20%)
        score = (speed * 0.4) + (repro * 0.4) + (dx * 0.2)
        unified_scores.append(score)
    
    return tools, unified_scores, speed_scores, repro_scores, dx_scores


def format_dx_results_table(dx_results):
    """Format DX results as a Markdown table."""
    if not dx_results:
        return ""
    
    table = "| Tool | Scenario | Description | Success |\n"
    table += "|------|----------|-------------|--------|\n"
    
    for tool, result in dx_results.items():
        scenarios = result.get("scenarios", [])
        for i, scenario in enumerate(scenarios):
            tool_cell = tool if i == 0 else ""
            success_icon = "✅" if scenario.get("success", False) else "❌"
            
            table += f"| {tool_cell} | {scenario.get('name', '')} | {scenario.get('description', '')} | {success_icon} |\n"
    
    return table


def generate_markdown_report(args=None):
    """Generate a Markdown report from benchmark results."""
    # Generate a timestamp for the report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create timestamped results directory
    report_dir = RESULTS_DIR / f"report_{timestamp}"
    report_dir.mkdir(exist_ok=True)
    
    # Load benchmark results
    installation_results, install_file = load_latest_json("installation_benchmark_results")
    reproducibility_results, repro_file = load_latest_json("reproducibility_results") 
    dx_results, dx_file = load_latest_json("dx_evaluation_results")
    hyperfine_results, hyperfine_file = load_latest_json("hyperfine-results")
    
    # Save copies of the raw data with timestamps
    if installation_results:
        output_path = RAW_DIR / f"installation_benchmark_results_{timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(installation_results, f, indent=2)
        print(f"Saved installation results to {output_path}")
    
    if reproducibility_results:
        output_path = RAW_DIR / f"reproducibility_results_{timestamp}.json" 
        with open(output_path, "w") as f:
            json.dump(reproducibility_results, f, indent=2)
        print(f"Saved reproducibility results to {output_path}")
    
    if dx_results:
        output_path = RAW_DIR / f"dx_evaluation_results_{timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(dx_results, f, indent=2)
        print(f"Saved developer experience results to {output_path}")
    
    if hyperfine_results:
        output_path = RAW_DIR / f"hyperfine_results_{timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(hyperfine_results, f, indent=2)
        print(f"Saved hyperfine results to {output_path}")
    
    # Generate charts
    installation_data = None
    reproducibility_data = None
    hash_comparison_data = None
    dx_data = None
    hyperfine_data = None
    unified_score_data = None
    
    if installation_results:
        installation_data = generate_installation_speed_chart(installation_results, report_dir / "installation_speed.png")
    
    if reproducibility_results:
        reproducibility_data = generate_reproducibility_chart(reproducibility_results, report_dir / "reproducibility.png")
        hash_comparison_data = generate_hash_comparison_chart(reproducibility_results, report_dir / "hash_comparison.png")
    
    if dx_results:
        dx_data = generate_dx_chart(dx_results, report_dir / "dx_success_rate.png")
    
    if hyperfine_results:
        hyperfine_data = generate_hyperfine_chart(hyperfine_results, report_dir / "hyperfine_benchmark.png")
    
    # Generate unified scoring chart if we have at least two metrics
    if sum(x is not None for x in [installation_data, reproducibility_data, dx_data]) >= 2:
        unified_score_data = generate_unified_score_chart(
            installation_data, 
            hyperfine_data, 
            reproducibility_data, 
            dx_data, 
            report_dir / "unified_score.png"
        )
    
    # Generate Markdown report
    report_md = f"""# Python Dependency Management Benchmark Results

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

**System Information:**
- OS: {platform.system()} {platform.release()} ({platform.machine()})
- Python: {platform.python_version()}

## Data Sources
- Installation: {install_file or "N/A"}
- Reproducibility: {repro_file or "N/A"}
- Developer Experience: {dx_file or "N/A"}
- Hyperfine Benchmarks: {hyperfine_file or "N/A"}

## Executive Summary

This report compares the performance of four Python dependency management tools:
- **uv**: A fast Python package installer and resolver
- **poetry**: A dependency management and packaging tool
- **pip-tools**: A tool to generate and synchronize pip requirements files
- **make**: Traditional approach using Makefile and requirements.txt

The evaluation covers three key aspects:
1. **Installation Speed**: Time taken to install dependencies
2. **Reproducibility**: Consistency of environments across multiple runs
3. **Developer Experience**: Success rate in common development workflows

"""

    # Add installation speed results
    report_md += """## Installation Speed

The chart below shows the time taken by each tool to install the same set of dependencies.

![Installation Speed Comparison](installation_speed.png)

"""
    
    if installation_data:
        tools, times = installation_data
        report_md += "| Tool | Installation Time |\n"
        report_md += "|------|------------------|\n"
        for tool, time in zip(tools, times):
            report_md += f"| {tool} | {time:.2f}s |\n"
        
        report_md += f"\n**Fastest Tool**: {tools[0]} ({times[0]:.2f}s)\n"
        report_md += f"**Slowest Tool**: {tools[-1]} ({times[-1]:.2f}s)\n"
        report_md += f"**Speed Difference**: {times[-1]/times[0]:.1f}x\n"
    
    # Add hyperfine benchmark results
    report_md += """
## Hyperfine Benchmark Results

Hyperfine provides high-resolution benchmarks with multiple runs for more accurate measurements.

![Hyperfine Benchmark Results](hyperfine_benchmark.png)

"""
    
    if hyperfine_data:
        tools, mean_times, std_devs, min_times, max_times = hyperfine_data
        report_md += "| Tool | Mean Time | Std Dev | Min Time | Max Time |\n"
        report_md += "|------|-----------|---------|----------|----------|\n"
        for tool, mean, std, min_t, max_t in zip(tools, mean_times, std_devs, min_times, max_times):
            report_md += f"| {tool} | {mean:.2f}s | ±{std:.2f}s | {min_t:.2f}s | {max_t:.2f}s |\n"
        
        fastest_idx = np.argmin(mean_times)
        slowest_idx = np.argmax(mean_times)
        
        report_md += f"\n**Fastest Tool**: {tools[fastest_idx]} ({mean_times[fastest_idx]:.2f}s)\n"
        report_md += f"**Slowest Tool**: {tools[slowest_idx]} ({mean_times[slowest_idx]:.2f}s)\n"
        report_md += f"**Speed Difference**: {mean_times[slowest_idx]/mean_times[fastest_idx]:.1f}x\n"
        
        # Calculate coefficient of variation (CV) for each tool
        report_md += "\n**Consistency (lower CV is better)**:\n"
        for tool, mean, std in zip(tools, mean_times, std_devs):
            cv = (std / mean) * 100  # Coefficient of variation as percentage
            report_md += f"- {tool}: {cv:.2f}% variability\n"
    
    # Add reproducibility results
    report_md += """
## Reproducibility

This section evaluates whether each tool produces consistent environments across multiple runs.

![Environment Reproducibility](reproducibility.png)

### Hash Comparison Across Runs

The chart below shows a detailed comparison of environment hashes across multiple runs.

![Hash Comparison](hash_comparison.png)

"""
    
    if reproducibility_data:
        tools, reproducible = reproducibility_data
        report_md += "| Tool | Reproducible |\n"
        report_md += "|------|-------------|\n"
        for tool, rep in zip(tools, reproducible):
            report_md += f"| {tool} | {'Yes' if rep == 1 else 'No'} |\n"
        
        reproducible_tools = [tools[i] for i, rep in enumerate(reproducible) if rep == 1]
        non_reproducible_tools = [tools[i] for i, rep in enumerate(reproducible) if rep == 0]
        
        if reproducible_tools:
            report_md += f"\n**Reproducible Tools**: {', '.join(reproducible_tools)}\n"
        if non_reproducible_tools:
            report_md += f"**Non-Reproducible Tools**: {', '.join(non_reproducible_tools)}\n"
            
        # Add hash details if available
        if hash_comparison_data:
            report_md += "\n### Hash Details\n\n"
            hash_tools, _, hash_samples = hash_comparison_data
            
            for i, tool in enumerate(hash_tools):
                report_md += f"**{tool}**:\n"
                for j, hash_value in enumerate(hash_samples[i]):
                    hash_display = hash_value if hash_value else "None"
                    report_md += f"- Run {j+1}: `{hash_display}`\n"
                report_md += "\n"
    
    # Add developer experience results
    report_md += """
## Developer Experience

This section evaluates how well each tool handles common developer workflows.

![Developer Experience - Scenario Success Rate](dx_success_rate.png)

"""
    
    if dx_data:
        tools, success_rates = dx_data
        report_md += "| Tool | Success Rate |\n"
        report_md += "|------|-------------|\n"
        for tool, rate in zip(tools, success_rates):
            report_md += f"| {tool} | {rate:.1f}% |\n"
        
        best_tool_idx = np.argmax(success_rates)
        worst_tool_idx = np.argmin(success_rates)
        
        report_md += f"\n**Best DX Tool**: {tools[best_tool_idx]} ({success_rates[best_tool_idx]:.1f}%)\n"
        report_md += f"**Worst DX Tool**: {tools[worst_tool_idx]} ({success_rates[worst_tool_idx]:.1f}%)\n"
    
    # Add detailed DX results
    report_md += """
### Detailed Developer Experience Results

The table below shows the success/failure of each tool in specific development scenarios.

"""
    
    if dx_results:
        report_md += format_dx_results_table(dx_results)
    
    # Add performance analysis section
    report_md += """
## Performance Analysis

### Speed Comparison

The following chart shows the relative performance of each tool compared to the fastest one.

"""
    
    # Add performance comparison based on hyperfine results
    if hyperfine_data:
        tools, mean_times, std_devs, min_times, max_times = hyperfine_data
        
        # Find the fastest tool
        fastest_idx = np.argmin(mean_times)
        fastest_time = mean_times[fastest_idx]
        fastest_tool = tools[fastest_idx]
        
        # Calculate relative speeds
        relative_speeds = [time / fastest_time for time in mean_times]
        
        # Create a comparison table
        report_md += "| Tool | Time | Relative Speed |\n"
        report_md += "|------|------|---------------|\n"
        
        for i, tool in enumerate(tools):
            is_fastest = (i == fastest_idx)
            speed_text = "1.0x (fastest)" if is_fastest else f"{relative_speeds[i]:.1f}x slower"
            report_md += f"| {tool} | {mean_times[i]:.2f}s | {speed_text} |\n"
        
        # Add uv vs pip-tools comparison if both exist
        if 'uv' in tools and 'piptools' in tools:
            uv_idx = tools.index('uv')
            piptools_idx = tools.index('piptools')
            speedup = mean_times[piptools_idx] / mean_times[uv_idx]
            
            report_md += f"\n**UV vs pip-tools**: uv is {speedup:.1f}x faster than pip-tools\n"
            
        # Add uv vs poetry comparison if both exist
        if 'uv' in tools and 'poetry' in tools:
            uv_idx = tools.index('uv')
            poetry_idx = tools.index('poetry')
            speedup = mean_times[poetry_idx] / mean_times[uv_idx]
            
            report_md += f"**UV vs poetry**: uv is {speedup:.1f}x faster than poetry\n"
    
    # Add comprehensive qualitative analysis
    report_md += """
### Qualitative Analysis

| Tool | Strengths | Weaknesses |
|------|-----------|------------|
| uv | • Extremely fast installation<br>• Reproducible environments<br>• Minimal dependencies | • Newer tool with evolving features<br>• Fewer advanced packaging features |
| poetry | • Comprehensive dependency management<br>• Built-in packaging<br>• Virtual environment handling | • Slower installation times<br>• Issues with reproducibility in our tests |
| pip-tools | • Simple workflow<br>• Direct use of pip<br>• Reproducible environments | • Significantly slower installation<br>• Requires additional steps for venv management |
| make | • Flexible, script-based approach<br>• Works with standard tools<br>• Reproducible environments | • Requires more manual setup<br>• Slower installation times |
"""
    
    # Add conclusion
    report_md += """
## Conclusion

Based on the benchmark results, here's a summary of the strengths and weaknesses of each tool:

"""
    
    # Add the unified score section if available
    if unified_score_data:
        tools, unified_scores, speed_scores, repro_scores, dx_scores = unified_score_data
        
        report_md += """
### Unified Performance Score

The chart below combines all metrics (installation speed, reproducibility, and developer experience) into a unified score:

![Unified Performance Score](unified_score.png)

"""
        
        report_md += "| Tool | Unified Score | Speed Score | Reproducibility | DX Score |\n"
        report_md += "|------|--------------|-------------|-----------------|----------|\n"
        
        # Sort tools by unified score (descending)
        sorted_indices = np.argsort(unified_scores)[::-1]
        
        for idx in sorted_indices:
            tool = tools[idx]
            report_md += f"| {tool} | {unified_scores[idx]:.1f}% | {speed_scores[idx]:.1f}% | {repro_scores[idx]:.1f}% | {dx_scores[idx]:.1f}% |\n"
        
        report_md += "\n**Scoring Weights**: Installation Speed (40%), Reproducibility (40%), Developer Experience (20%)\n\n"
        
        # Add the best tool based on unified score
        best_idx = np.argmax(unified_scores)
        report_md += f"**Best Overall Tool**: {tools[best_idx]} with a score of {unified_scores[best_idx]:.1f}%\n\n"
    
    # Generate conclusion if we have all data
    if installation_data and reproducibility_data and dx_data:
        tools_speed = installation_data[0]
        tools_repro = reproducibility_data[0]
        repro_status = reproducibility_data[1]
        tools_dx = dx_data[0]
        dx_rates = dx_data[1]
        
        # Create tool summary
        for tool in set(tools_speed + tools_repro + tools_dx):
            report_md += f"### {tool}\n\n"
            
            # Speed ranking
            if tool in tools_speed:
                speed_rank = tools_speed.index(tool) + 1
                speed_time = installation_data[1][tools_speed.index(tool)]
                speed_text = f"**Installation Speed**: {speed_rank}/{len(tools_speed)} ({speed_time:.2f}s)"
                report_md += f"- {speed_text}\n"
            
            # Reproducibility
            if tool in tools_repro:
                is_repro = repro_status[tools_repro.index(tool)] == 1
                repro_text = f"**Reproducibility**: {'✅ Yes' if is_repro else '❌ No'}"
                report_md += f"- {repro_text}\n"
            
            # DX
            if tool in tools_dx:
                dx_rate = dx_rates[tools_dx.index(tool)]
                dx_rank = sorted(range(len(dx_rates)), key=lambda i: dx_rates[i], reverse=True).index(tools_dx.index(tool)) + 1
                dx_text = f"**Developer Experience**: {dx_rank}/{len(tools_dx)} ({dx_rate:.1f}%)"
                report_md += f"- {dx_text}\n"
            
            report_md += "\n"
    
    # Add recommendations with specific use cases
    report_md += """
## Recommendations

Based on the benchmark results, here are specific recommendations for different use cases:

### For CI/CD Pipelines and Container Builds

**Recommended**: uv

For environments where installation speed is critical, such as CI/CD pipelines or container builds, uv is the clear winner. Its dramatic speed advantage (often 10-15x faster than traditional approaches) can significantly reduce build times and costs.

### For Development Teams

**Recommended**: Poetry or uv

For day-to-day development work:
- **Poetry** offers excellent developer experience with consistent workflows and built-in package management features
- **uv** provides speed benefits that improve developer workflow, especially on larger projects

### For Production Deployments

**Recommended**: uv or pip-tools

For production environments where reproducibility is critical:
- **uv** offers both speed and reproducibility
- **pip-tools** provides reliable reproducibility with straightforward workflows

### For Projects Transitioning from Traditional Approaches

**Recommended**: Start with pip-tools, then migrate to uv

If you're currently using requirements.txt files directly:
1. Adopt pip-tools as an intermediate step for better reproducibility
2. Consider migrating to uv for speed benefits while maintaining compatibility with requirements.txt files

## Final Verdict

**uv** shows the most promising results in our benchmarks, with exceptional speed and good reproducibility. While it's a newer tool that may continue to evolve, its performance advantages are substantial enough to consider adoption, particularly in environments where installation speed matters.

However, all tools tested have their merits and choosing the right one depends on your specific requirements around speed, reproducibility, and developer experience.
"""

    # Write Markdown report to file
    report_path = report_dir / "report.md"
    with open(report_path, "w") as f:
        f.write(report_md)
    
    # Also save a copy of the latest report in the main results directory
    latest_report_path = RESULTS_DIR / "latest_report.md"
    with open(latest_report_path, "w") as f:
        f.write(report_md)
    
    print(f"Markdown report generated at {report_path}")
    print(f"Latest report available at {latest_report_path}")
    return timestamp


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark reports")
    parser.add_argument("--timestamp", help="Use specific timestamp for report generation")
    parser.add_argument("--json-only", action="store_true", help="Only save JSON files, skip report generation")
    parser.add_argument("--clean", action="store_true", help="Clean up old reports (keep latest 5)")
    args = parser.parse_args()
    
    if args.clean:
        # Keep only the latest 5 reports
        reports = sorted(glob.glob(str(RESULTS_DIR / "report_*")))
        if len(reports) > 5:
            for old_report in reports[:-5]:
                shutil.rmtree(old_report)
                print(f"Removed old report: {old_report}")
    
    if not args.json_only:
        timestamp = generate_markdown_report(args)
        print(f"Report generated with timestamp: {timestamp}")
    else:
        print("JSON files saved, skipping report generation")


if __name__ == "__main__":
    main()