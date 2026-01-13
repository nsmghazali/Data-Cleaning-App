import streamlit as st
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title='Clean Your Data', page_icon= '🧹', layout='wide')

st.title('🧹🧹 Data Cleaning App')
st.write('Upload A **CSV** or An **Excel** File To Clean Your Data. This App Lets You to Download The Cleaned Data in CSV format.')

# for uploading file
uploaded_file = st.file_uploader('📁 Upload A .CSV or .XLSX File. XLS files are not supported.', type=['csv','xlsx'])

if uploaded_file is not None:
    try:
        
        # Get file extension
        file_name = uploaded_file.name
        st.write(uploaded_file.name)

        if file_name.endswith(".csv"):
            data = pd.read_csv(uploaded_file)

        elif file_name.endswith(".xlsx"):
            data = pd.read_excel(uploaded_file)

        # streamlit read boolean as checkboxes
        # converting boolean values to str 
        bool_cols = data.select_dtypes(include=['bool']).columns
        data[bool_cols] = data[bool_cols].astype('str')
    except Exception as e:
        st.error('Could Not Read Your File. Please Check The File Format.')
        st.exception(e)
        st.stop

    st.success('✅ File Uploaded Successfully!')

    # explicitly convert date-like columns (if any) to datetime before calling st.dataframe()
    for col in data.columns:
        if data[col].dtype == "object":
            try:
                data[col] = pd.to_datetime(data[col], errors="raise")
            except Exception:
                pass  # keep as string if not a date

        # Preview of Data
    st.write('### Preview Of Data')
    st.dataframe(data.head()) # display table

    # Data Overview
    st.write('### Data Overview')
    # how many rows
    st.write('No of Rows', data.shape[0])
    # how many columns
    st.write('No of Columns', data.shape[1])

    st.write('### ❓ Missing Values Per Column')
    missing_pct = (data.isnull().sum() / len(data) * 100).round(2)
    missing_count = data.isnull().sum()
    # Create missing_summary dataframe
    missing_summary = pd.DataFrame({
        "Column": data.columns,
        "Missing values": missing_count,
        "Missing (%)": missing_pct,
        #"Duplicate Values": data[col].duplicated().sum()
        })

    styled_df = missing_summary.style.apply(lambda x: [
        'background-color: #fdecea; color: #b71c1c' if v > 50 else
        'background-color: #fff8e1' if v > 20 else ''
        for v in missing_summary['Missing (%)']
    ], axis=0)

    st.dataframe(styled_df)

    # Identify columns based on missing %
    drop_cols = missing_summary[missing_summary['Missing (%)'] > 50]['Column'].tolist()
    fill_drop_cols = missing_summary[(missing_summary['Missing (%)'] > 20) & 
                                    (missing_summary['Missing (%)'] <= 50)]['Column'].tolist()

    # Show **one combined warning/info**
    if drop_cols:
        st.warning(f"‼️ Consider dropping these columns due to high missing values (more than 50%): \n {', '.join(drop_cols)}")

    if fill_drop_cols:
        st.warning(f"⚠️ Consider filling or dropping these columns (missing 20-50%): \n {', '.join(fill_drop_cols)}")

    st.write('### 📑 Duplicated Values Per Column')
    
    # Create duplicated_summary dataframe
    dupl_summary = pd.DataFrame({
        "Column": data.columns,
        "Duplicate Values": [data[col].duplicated().sum() for col in data.columns]
        })
    
    # Show message if no duplicates at all
    if dupl_summary['Duplicate Values'].sum() == 0:
        st.info("✅ There are no duplicated values in the dataset")
    else:
        st.dataframe(dupl_summary)

    # create a copy and wroking data
    if 'copied_data' not in st.session_state:
        st.session_state.copied_data = data.copy()
    
    # assign to local var for convenience
    copied_data = st.session_state.copied_data

    st.write('### 🧹 Handling Missing Values')
    columns = copied_data.columns.tolist()
    selected_col = st.selectbox('Choose A Column', ["--None--"] + columns)
    actions = st.selectbox('Choose An Action', ["--None--", "Fill Missing", "Drop Column"])
    
    if selected_col != "--None--" and actions != "--None--":
        if actions == 'Fill Missing':
            # check whether it's numeric or non-numeric
            is_numeric = copied_data[selected_col].dtype != 'object'
            # method options depend on the column whether its categorical or numerical
            methods = ['mean', 'median'] if is_numeric else ['mode', 'constant']
            method_tofill = st.selectbox('Choose How to Fill The Missing Values',methods)
            value = None
            if method_tofill == "constant":
                value = st.text_input("Enter value to fill missing with")

    # Applying desired actions only when button is clicked
    if st.button("Apply"):
        if actions == 'Fill Missing':
            if method_tofill == 'mean':
                copied_data[selected_col].fillna(copied_data[selected_col].mean(),inplace=True)
            elif method_tofill == 'median':
                copied_data[selected_col].fillna(copied_data[selected_col].median(),inplace=True)
            elif method_tofill == 'mode':
                copied_data[selected_col].fillna(copied_data[selected_col].mode()[0],inplace=True)
            elif method_tofill == 'constant' and value is not None:
                copied_data[selected_col].fillna("value",inplace=True)
            st.session_state.copied_data = copied_data
            st.success(f"Filled missing values for {selected_col}")
        elif actions == 'Drop Column':
            copied_data = copied_data.drop(columns=[selected_col])
            st.session_state.copied_data = copied_data
            st.success(f"Dropped column {selected_col}")

        st.write("### Preview of Cleaned Data")
        st.dataframe(copied_data.head())
    
    # Section only appears if there's duplicated values
    if dupl_summary['Duplicate Values'].sum() > 0:
        st.write('### ✂️ Handling Missing Values')
        if st.button("Drop Duplicate Rows"):
            before = len(copied_data)
            cleaned_data = copied_data.drop_duplicates()
            after = len(copied_data)
            st.session_state.copied_data = copied_data
            st.success(f"Dropped {before - after} duplicate rows")

    # Download Cleaned Data
    csv = copied_data.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Cleaned Data (CSV)",
        data=csv,
        file_name='cleaned_data.csv',
        mime='text/csv'
    )

       
else:
    st.info('Please Upload A .CSV Or .XLSX File To Get Started. XLS File Is Not Supported.')