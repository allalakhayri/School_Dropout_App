import os
from flask import Flask, render_template, request, jsonify
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from werkzeug.utils import secure_filename
from flask_cors import CORS
import  time ,sqlite3 , json 
import seaborn as sns
import matplotlib.pyplot as plt
import random
from sklearn.impute import SimpleImputer




def create_connection():
    conn = sqlite3.connect('comments.db', check_same_thread=False , timeout=10)
    c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS comments
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              stats TEXT,
              cat_cols TEXT,
              num_cols TEXT,
              time_taken REAL,
              comment TEXT NOT NULL,
              CONSTRAINT comment_required CHECK (comment != ''))''')
    conn.commit()
    return conn

app = Flask(__name__)
CORS(app, supports_credentials=True, allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"])
df=None
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/upload', methods=['POST'])
def upload():
    global df 
    try:
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided.'}), 400
        
        # Get file and filename
        file = request.files['file']
        filename = secure_filename(file.filename)

        # Check if file format is supported
        file_format = os.path.splitext(filename)[1]
        if file_format not in ['.csv', '.txt', '.xlsx']:
            return jsonify({'error': 'Unsupported file format.'}), 400

        # Read file into pandas DataFrame
        if file_format == '.xlsx':
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

        # Convert DataFrame to CSV format
        csv_data = df.to_csv(index=False)
       
        
        # Return success response      
        return jsonify({'data': csv_data}), 200
    
    except FileNotFoundError:
        return jsonify({'error': 'No file found.'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/preprocess', methods=['POST'])
def preprocess():
        data = request.get_json()
        df = pd.DataFrame(data)  
        start_time = time.time()
        # Drop null values
        df = df.dropna()
        df = df.dropna(axis=1) 
        # Select categorical and numerical features
        cat_cols = []
        num_cols = []
        for col in df.columns:
                try : 
                     pd.to_numeric(df[col])
                     num_cols.append(col)
                except:
                     cat_cols.append(col)  
        df = df.replace('', '0') # replace empty strings with 0
        df = df.apply(pd.to_numeric, errors='coerce')
        null_counts=df.isnull().sum().to_dict()

        print(df['Target']) 
       
        if 'Target' in cat_cols:
            df = df.drop('Target', axis=1)

        # Compute basic statistics
        stats = {}
        stats['min'] = df.min().to_dict()
        stats['max'] = df.max().to_dict()
        stats['std'] = df.std().to_dict()
        stats['median'] = df.median().to_dict()
        stats['range'] = (df.max()-df.min()).to_dict()
        stats['null_count'] =null_counts
        # Format statistics for display
        formatted_stats = {
    'Minimum': '   --   '.join([f'{col}: {val}' for col, val in stats['min'].items()]),
    'Maximum': '   --   '.join([f'{col}: {val}' for col, val in stats['max'].items()]),
    'Standard Deviation': '  --  '.join([f'{col}: {val:.1f}' for col, val in stats['std'].items()]),
    'Median': '  --  '.join([f'{col}: {val:.1f}' for col, val in stats['median'].items()]),
    'Range': '  --  '.join([f'{col}: {val:.1f}' for col, val in stats['range'].items()]),
    'Null Counts': ' --  '.join([f'{col}: {val:.1f}' for col, val in stats['null_count'].items()])
}
        
    # Detect outliers using IQR
        outliers = {}
        for col in num_cols:
            q1, q3 = np.percentile(df[col], [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            outliers[col] = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col].tolist()


    # Convert the dataframe to a dictionary with lists
        df_dict = df.to_dict(orient='split')
        df.replace(to_replace=r'\r', value='', regex=True, inplace=True)
        # Create a list to store plots
        plots = []

       

    
        end_time = time.time()
        time_taken = int(end_time - start_time)*1000

        # Return preprocessed data
        preprocessed_data = {
            'data': df_dict,
            'cat_cols': cat_cols,
            'num_cols': num_cols,
            'formatted_stats': formatted_stats,
            'time_taken': time_taken,
            'outliers': outliers,
            'plots':plots
        }
        return jsonify(preprocessed_data), 200


@app.route('/comments', methods=['POST'])
def submit_comment():
    conn = create_connection()
    c = conn.cursor()
    stats = request.json.get('stats',None)
    cat_cols = request.json.get('cat_cols' , None)
    num_cols = request.json.get('num_cols', None)
    time_taken = request.json.get('time_taken', None)
    comment = request.json['comment'] 
    
    c.execute('''INSERT INTO comments (stats, cat_cols, num_cols, time_taken, comment)
                 VALUES (?, ?, ?, ?, ?)''',
              (json.dumps(stats), json.dumps(cat_cols), json.dumps(num_cols), time_taken, comment))
    
    conn.commit()
    conn.close()
    return jsonify({'message':'Comment submitted successfully'}), 200

@app.route('/visualise', methods=['POST'])
def visualise():
        data = request.get_json()
        df = pd.DataFrame(data)
        start_time = time.time()
        df = df.dropna()
        df = df.dropna(axis=1)  
      # Create an empty list to store plots
        plots = []
         # Select categorical and numerical features
        cat_cols = []
        num_cols = []
        for col in df.columns:
                try : 
                     pd.to_numeric(df[col])
                     num_cols.append(col)
                except:
                     cat_cols.append(col)  
        df = df.replace('', '0') # replace empty strings with 0
        df = df.apply(pd.to_numeric, errors='coerce')
        null_counts=df.isnull().sum().to_dict()

        print(df['Target']) 
       
        if 'Target' in cat_cols:
            df = df.drop('Target', axis=1)
        # Compute basic statistics
        stats = {}
        stats['min'] = df.min().to_dict()
        stats['max'] = df.max().to_dict()
        stats['std'] = df.std().to_dict()
        stats['median'] = df.median().to_dict()
        stats['range'] = (df.max()-df.min()).to_dict()
        stats['null_count'] =null_counts

        # Detect outliers using IQR
        outliers = {}
        for col in num_cols:
            q1, q3 = np.percentile(df[col], [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            outliers[col] = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col].tolist()
         # Set color scheme
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#004747']

        # Create a figure and axes
        fig, ax = plt.subplots()

        # Plot minimum values
        ax.bar(stats['min'].keys(), stats['min'].values(), color=colors[0])
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Minimum values')
        plots.append('minimum.png')
        filename = os.path.join('static', 'minimum.png')
        plt.savefig(filename, bbox_inches='tight', dpi=150)
        plt.clf()
        plt.close()

        # Create a new figure and axes
        fig, ax = plt.subplots()

        # Plot maximum values
        ax.bar(stats['max'].keys(), stats['max'].values(), color=colors[1])
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Maximum values')
        plots.append('maximum.png')
        filename = os.path.join('static', 'maximum.png')
        plt.savefig(filename, bbox_inches='tight', dpi=150)
        plt.clf()
        plt.close()

        # Create a new figure and axes
        fig, ax = plt.subplots()

        # Plot standard deviation values
        ax.bar(stats['std'].keys(), stats['std'].values(), color=colors[2])
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Standard deviation values')
        plots.append('std.png')
        filename = os.path.join('static', 'std.png')
        plt.savefig(filename, bbox_inches='tight', dpi=150)
        plt.clf()
        plt.close()

        # Create a new figure and axes
        fig, ax = plt.subplots()

        # Plot median values
        ax.bar(stats['median'].keys(), stats['median'].values(), color=colors[3])
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Median values')
        plots.append('median.png')
        filename = os.path.join('static', 'median.png')
        plt.savefig(filename, bbox_inches='tight', dpi=150)
        plt.clf()
        plt.close()

        # Create a new figure and axes
        fig, ax = plt.subplots()

        # Plot range values
        ax.bar(stats['range'].keys(), stats['range'].values(), color=colors[4])
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Range values')
        plots.append('range.png')
        filename = os.path.join('static', 'range.png')
        plt.savefig(filename, bbox_inches='tight', dpi=150)
        plt.clf()
        plt.close()

        # Create a new figure and axes
        fig, ax = plt.subplots(figsize=(8, 9))

        # Plot null counts values
        ax.bar(stats['null_count'].keys(), stats['null_count'].values(), color=colors[5])
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Null counts')
        plots.append('null_counts.png')
        filename = os.path.join('static', 'null_counts.png')
        plt.savefig(filename, bbox_inches='tight', dpi=150)
        plt.clf()
        plt.close()
         # Create boxplot with red dots for outliers
        fig, ax = plt.subplots(figsize=(10,6))
        bp = ax.boxplot(df[num_cols].values, patch_artist=True, notch=True)

        # Customize boxplot colors and labels
        colors = ['#66b3ff', '#99ff99', '#ffcc99', '#ff9999']
        labels = ['Normal', 'Slightly\nElevated', 'Moderately\nElevated', 'Highly\nElevated']
        for patch, color, label in zip(bp['boxes'], colors, labels):
            patch.set_facecolor(color)
            patch.set_label(label)
        ax.set_xticklabels(num_cols, rotation=45, ha='right')
        ax.set_xlabel('Numerical Columns')
        ax.set_ylabel('Value')
        ax.set_title('Distribution of Numerical Columns with Outliers')

        # Highlight outliers with red dots
        for i, col in enumerate(num_cols):
            outliers_col = outliers[col]
            if outliers_col:
                for outlier in outliers_col:
                    ax.plot(i+1, outlier, 'ro', markersize=5)

        # Add legend for boxplot colors and outlier dots
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label='Outlier',
                markerfacecolor='r', markersize=5),
            Patch(facecolor=colors[0], edgecolor='k', label=labels[0]),
            Patch(facecolor=colors[1], edgecolor='k', label=labels[1]),
            Patch(facecolor=colors[2], edgecolor='k', label=labels[2]),
            Patch(facecolor=colors[3], edgecolor='k', label=labels[3])
        ]
        ax.legend(handles=legend_elements, loc='best')

        plots.append('outliers.png')
        filename = os.path.join('static', 'outliers.png')
        plt.savefig(filename, bbox_inches='tight', dpi=150)
        plt.clf()
        plt.close()









        corr_matrix = df.corr()
  
        if corr_matrix.empty:
            raise ValueError('Empty correlation matrix')
        plt.figure(figsize=(20, 15))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
        plt.title('Correlation Matrix')
        # Save the plot to a PNG file and store it in the plots list
        filename = os.path.join('static', f'correlation_matrix.png')
        plt.savefig(filename) 
        plots.append(f'correlation_matrix.png')
        plt.close()   
        
        columns = df.columns.tolist()
         # Loop through each column and create a plot
        for column in columns:
            column_name = column.split('/')[0]
            df = df.rename(columns={column: column_name})
        # for categorical features, plot a countplot
            if df[column_name].dtype == 'object':
                plt.figure(figsize=(10,6))
                sns.countplot(data=df,x=column_name)
                plt.xticks(rotation=45) 
                plt.title(f"Distribution of {column_name}") 
                plt.xlabel(column_name) 
                plt.ylabel("Count") 
            # Save the plot to a PNG file and store it in the plots list
                filename = os.path.join('static', f'{column_name}.png')
                plt.savefig(filename,dpi=150)             
                plots.append(f'{column_name}.png')
                plt.close()
            
        # for numerical features, plot a histogram
            else:
              plt.figure(figsize=(12,5))
              sns.histplot(data=df,x=column_name,kde=True) 
              plt.title(f"Distribution of {column_name}") 
              plt.xlabel(column_name) 
              plt.ylabel("Count") 
              # Save the plot to a PNG file and store it in the plots list
              filename = os.path.join('static', f'{column_name}.png')
              plt.savefig(filename,dpi=150) 
              plots.append(f'{column_name}.png')
              plt.close()
       
        
      
        for i in range(5):
# select two columns randomly
            x_col, y_col = random.sample(df.columns.tolist(), 2)
          # create a scatter plot
            plt.figure(figsize=(10,6))
            sns.scatterplot(data=df, x=x_col, y=y_col)
            plt.title(f"Scatter plot of {x_col} vs {y_col}")
            plt.xlabel(x_col) 
            plt.ylabel(y_col) 
        # Save the plot to a PNG file and store it in the plots list
            filename = os.path.join('static', f'{x_col}_vs_{y_col}.png')
            plt.savefig(filename) 
            plots.append(f'{x_col}_vs_{y_col}.png')
            plt.close()
        end_time = time.time()
        time_taken = int((end_time - start_time))*1000
        visualised_data = {
            'data':plots,
            'time_taken': time_taken,
        }
      # Pass the list of plots to the template
        return jsonify(visualised_data), 200
# Get a list of all the files in the static folder
files = os.listdir('static')

# Loop through each file and delete it
for file in files:
    if file.endswith('.png'):
        os.remove(os.path.join('static', file))

@app.route('/process', methods=['POST'])
def process():
        data = request.get_json()
        start_time = time.time()
        df = pd.DataFrame(data)
        df = df.dropna()
        df = df.dropna(axis=1) 
        cat_cols = []
        num_cols = []
        for col in df.columns:
                try : 
                     pd.to_numeric(df[col])
                     num_cols.append(col)
                except:
                     cat_cols.append(col)
        target_column = cat_cols[0]
        X = df.drop(target_column, axis=1)
        X = X.apply(pd.to_numeric, errors='coerce')

        y = df[target_column]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        imputer = SimpleImputer(strategy='median')
        X_train = imputer.fit_transform(X_train)
        X_test = imputer.transform(X_test)

        n=12
        # Fit a Random Forest model and calculate feature importances
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        rf_importances = permutation_importance(rf, X_test, y_test, n_repeats=10, random_state=42)
        feature_importances = rf_importances.importances_mean
        # Convert feature importances to a dictionary
        feature_importances_dict = {}
        for i, col in enumerate(X.columns):
            feature_importances_dict[col] = feature_importances[i]
            # filter out features with null importance scores
        non_null_importances = {k: v for k, v in feature_importances_dict.items() if v > 0.0}
        # Select top n features based on their importance
        top_n_features = dict(sorted(non_null_importances.items(), key=lambda item: item[1], reverse=True)[:n])

        json_data = json.dumps(top_n_features)
        end_time = time.time()
        time_taken = int((end_time - start_time))*1000
        processed_data = {
            'feature_importances':json_data,
            'time_taken': time_taken,
        }
        return jsonify(processed_data), 200

if __name__ == '__main__':
        app.run(debug=True)
