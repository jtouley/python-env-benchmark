"""
Generate a comprehensive Markdown report from benchmark results.
"""

import json
import os
from datetime import datetime
import platform
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Create results directory if it doesn't exist
RESULTS_DIR = Path("benchmark_results")
RESULTS_DIR.mkdir(exist_ok=True)


def load_json_file(filename):
    """Load a JSON file if it exists, otherwise return None."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return None


def generate_installation_speed_chart(data, output_file):
    """Generate a bar chart for installation speed."""
    if not data:
        return
    
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
        return
    
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


def generate_dx_chart(data, output_file):
    """Generate a chart for developer experience results."""
    if not data:
        return
    
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


def generate_markdown_report():
    """Generate a Markdown report from all benchmark results."""
    # Load benchmark results
    installation_results = load_json_file("installation_benchmark_results.json")
    reproducibility_results = load_json_file("reproducibility_results.json")
    dx_results = load_json_file("dx_evaluation_results.json")
    
    # Generate charts
    installation_data = None
    reproducibility_data = None
    dx_data = None
    
    if installation_results:
        installation_data = generate_installation_speed_chart(installation_results, RESULTS_DIR / "installation_speed.png")
    
    if reproducibility_results:
        reproducibility_data = generate_reproducibility_chart(reproducibility_results, RESULTS_DIR / "reproducibility.png")
    
    if dx_results:
        dx_data = generate_dx_chart(dx_results, RESULTS_DIR / "dx_success_rate.png")
    
    # Generate Markdown report
    report_md = f"""# Python Dependency Management Benchmark Results

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

**System Information:**
- OS: {platform.system()} {platform.release()} ({platform.machine()})
- Python: {platform.python_version()}

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

![Installation Speed Comparison](benchmark_results/installation_speed.png)

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
    
    # Add reproducibility results
    report_md += """
## Reproducibility

This section evaluates whether each tool produces consistent environments across multiple runs.

![Environment Reproducibility](benchmark_results/reproducibility.png)

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
    
    # Add developer experience results
    report_md += """
## Developer Experience

This section evaluates how well each tool handles common developer workflows.

![Developer Experience - Scenario Success Rate](benchmark_results/dx_success_rate.png)

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
    
    # Add conclusion
    report_md += """
## Conclusion

Based on the benchmark results, here's a summary of the strengths and weaknesses of each tool:

"""
    
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
    
    # Add recommendations
    report_md += """
## Recommendations

Based on the benchmark results, here are some recommendations for different use cases:

1. **For speed-critical environments** (CI/CD pipelines, container builds):
   - Choose the fastest tool that meets your reproducibility requirements

2. **For development teams**:
   - Prioritize tools with better developer experience and clear error messages

3. **For production deployments**:
   - Prioritize tools with perfect reproducibility

4. **For balanced approaches**:
   - Consider the tool with the best overall ranking across all categories
"""

    # Write Markdown report to file
    with open(RESULTS_DIR / "report.md", "w") as f:
        f.write(report_md)
    
    print(f"Markdown report generated at {RESULTS_DIR}/report.md")


if __name__ == "__main__":
    generate_markdown_report()