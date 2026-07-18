import argparse
import os
import re
from pathlib import Path
import matplotlib.pyplot as plt

def parse_and_plot_logs(log_path, output_image_path, hide_plot=False):
    log_path = Path(log_path)
    
    if not log_path.exists():
        print(f"Error: Log file '{log_path}' not found.")
        return

    iterations = []
    losses = []
    depth_losses = []

    # Regex tailored to extract: current_iteration, Loss, and Depth Loss
    # Matches strings like: "29540/30000 ..., Loss=0.0189534, Depth Loss=0.0000000]"
    log_pattern = re.compile(
        r"(\d+)/\d+ .*Loss=([0-9\.]+),\s*Depth Loss=([0-9\.]+)"
    )

    print(f"Reading and parsing: {log_path.name}...")
    
    # Stream the file line-by-line for a constant memory footprint
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                iter_val = int(match.group(1))
                loss_val = float(match.group(2))
                depth_loss_val = float(match.group(3))
                
                iterations.append(iter_val)
                losses.append(loss_val)
                depth_losses.append(depth_loss_val)

    if not iterations:
        print("Warning: No matching training progress data found in the log file.")
        return

    print(f"Successfully parsed {len(iterations)} data points. Generating plot...")

    # Configure matplotlib to run without a GUI backend if --no-show is active
    if hide_plot:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend (saves file without popping up a window)

    # Plotting logic
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, losses, label="Total Loss", color="royalblue", alpha=0.8)
    
    # Check if Depth Loss actually changes, if it's always 0 we can just note it or plot it lightly
    if any(d > 0 for d in depth_losses):
        plt.plot(iterations, depth_losses, label="Depth Loss", color="orange", alpha=0.8, linestyle="--")

    plt.title("Neural Network Training Progress", fontsize=14, fontweight="bold")
    plt.xlabel("Iterations", fontsize=12)
    plt.ylabel("Loss Value", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()

    # Save image
    out_path = Path(output_image_path)
    plt.savefig(out_path, dpi=200)
    print(f"Plot image successfully saved to: {out_path.resolve()}")

    # Pop open window only if allowed
    if not hide_plot:
        plt.show()
        
    plt.close()

def main():
    parser = argparse.ArgumentParser(
        description="Extract training loss from custom tqdm/progress logs and plot them using Matplotlib."
    )
    
    # Required positional argument
    parser.add_argument(
        "log_file", 
        type=str, 
        help="Path to the training log file."
    )
    
    # Optional image path argument
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        help="Path where the output plot image should be saved (Default: loss_plot.png)"
    )
    
    # Flag to disable plt.show()
    parser.add_argument(
        "--no-show", 
        action="store_true", 
        help="If set, saves the image silently to disk without popping open a window GUI."
    )

    args = parser.parse_args()
    
    if not args.output:
        dirname = os.path.dirname(args.log_file)
        output_file = os.path.join(dirname, "train_loss.png")
    else:
        output_file = args.output

    parse_and_plot_logs(
        log_path=args.log_file, 
        output_image_path=output_file, 
        hide_plot=args.no_show
    )

if __name__ == "__main__":
    main()