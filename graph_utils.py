import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO

matplotlib.use('Agg') # Use non-interactive backend

def generate_report_graph(record):
    """
    Generates a bar chart for the student record and returns it as a BytesIO buffer.
    """
    plt.figure(figsize=(10, 6))
    categories = ['Hours Studied (x4)', 'Previous Score', 'Sleep Hours (x4)', 'Predicted Retention']
    # Normalize values for better visualization (scaling hours up)
    plot_values = [record.hours_studied * 4, record.previous_score, record.sleep_hours * 4, record.predicted_retention]
    
    bars = plt.bar(categories, plot_values, color=['#6366f1', '#a855f7', '#ec4899', '#10b981'])
    plt.title(f"Memory Retention Analysis: {record.student_name}", fontsize=14, pad=20)
    plt.ylabel('Score / Value (0-100 Scale)', fontsize=12)
    plt.ylim(0, 110)
    
    # Add values on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{round(yval, 1)}', ha='center', va='bottom')

    plt.tight_layout()
    img_stream = BytesIO()
    plt.savefig(img_stream, format='png', dpi=150)
    img_stream.seek(0)
    plt.close()
    return img_stream

def generate_bulk_dashboard_graphs(df):
    """
    Generates summary graphs for the bulk report.
    """
    graphs = {}
    
    # Graph 1: Retention vs Hours Studied (Scatter)
    plt.figure(figsize=(10, 6))
    plt.scatter(df['hours_studied'], df['retention_score'], color='#6366f1', alpha=0.6)
    plt.title('Retention Score vs. Hours Studied')
    plt.xlabel('Hours Studied')
    plt.ylabel('Retention Score (%)')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    buf1 = BytesIO()
    plt.savefig(buf1, format='png', dpi=150)
    buf1.seek(0)
    graphs['scatter'] = buf1
    plt.close()

    # Graph 2: Sleep Impact (Bar)
    plt.figure(figsize=(10, 6))
    # Group by rounded sleep hours for better visualization
    df_sleep = df.groupby(df['sleep_hours'].round())['retention_score'].mean().reset_index()
    plt.bar(df_sleep['sleep_hours'], df_sleep['retention_score'], color='#ec4899', alpha=0.7)
    plt.title('Average Retention Score by Sleep Hours')
    plt.xlabel('Sleep Hours')
    plt.ylabel('Avg Retention Score (%)')
    
    buf2 = BytesIO()
    plt.savefig(buf2, format='png', dpi=150)
    buf2.seek(0)
    graphs['sleep'] = buf2
    plt.close()

    return graphs
