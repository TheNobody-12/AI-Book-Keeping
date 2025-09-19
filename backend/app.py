from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import glob
import re

app = Flask(__name__)

def load_bank_statements():
    """Load bank statement data from structured JSON; fallback to CSV pairs.

    Priority:
    1) output/bank_statements/*_bank_statement.json (structured)
    2) CSV fallback by pairing *_summary.csv with *_all_transactions.csv
       found under output/bank_statements or output
    """
    statements = []
    json_dir = 'output/bank_statements'

    # First preference: structured JSON files
    if os.path.exists(json_dir):
        for file in os.listdir(json_dir):
            if file.endswith('_bank_statement.json'):
                try:
                    with open(os.path.join(json_dir, file), 'r') as f:
                        payload = json.load(f)
                        if isinstance(payload, list):
                            statements.extend(payload)
                        elif isinstance(payload, dict):
                            statements.append(payload)
                except Exception as e:
                    print(f"Error reading file {file}: {str(e)}")

    if statements:
        return statements

    # Fallback: construct from CSVs
    # Look in both bank_statements subfolder and root output
    csv_dirs = ['output/bank_statements', 'output']

    def money_to_float(x):
        if x is None or x == '' or (isinstance(x, float) and pd.isna(x)):
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        # remove currency symbols and commas
        try:
            return float(re.sub(r'[^0-9\.-]', '', str(x)))
        except Exception:
            return 0.0

    def parse_period(period_str):
        start = ''
        end = ''
        if isinstance(period_str, str) and 'to' in period_str:
            parts = [p.strip() for p in period_str.split('to', 1)]
            if len(parts) == 2:
                start, end = parts
        return start, end

    found_any = False
    for d in csv_dirs:
        if not os.path.exists(d):
            continue
        # find summary files
        for summary_path in glob.glob(os.path.join(d, '*_summary.csv')):
            base = os.path.basename(summary_path).replace('_summary.csv', '')
            transactions_path = os.path.join(d, f"{base}_all_transactions.csv")
            if not os.path.exists(transactions_path):
                # if not in same folder, try alternate folders
                alt = [p for p in csv_dirs if os.path.exists(os.path.join(p, f"{base}_all_transactions.csv"))]
                if alt:
                    transactions_path = os.path.join(alt[0], f"{base}_all_transactions.csv")
                else:
                    continue

            try:
                df_summary = pd.read_csv(summary_path)
                df_tx = pd.read_csv(transactions_path)
            except Exception as e:
                print(f"Error reading CSVs for base {base}: {e}")
                continue

            # Normalize columns if needed
            expected_summary_cols = {
                'Client Name', 'Bank Name', 'Account Number', 'Statement Period',
                'Beginning Balance', 'Ending Balance'
            }
            if not expected_summary_cols.issubset(set(df_summary.columns)):
                print(f"Summary CSV columns not as expected for {summary_path}")
                continue

            # Group by account number to build accounts list
            accounts = []
            # Fill NaN Account Number in transactions with the one from summary when possible
            acct_numbers = df_summary['Account Number'].dropna().astype(str).unique().tolist()
            df_tx['Account Number'] = df_tx['Account Number'].fillna('')
            # Build per-account
            for _, row in df_summary.iterrows():
                acct_num = str(row['Account Number']) if pd.notna(row['Account Number']) else ''
                begin_bal = money_to_float(row['Beginning Balance'])
                end_bal = money_to_float(row['Ending Balance'])

                # Match transactions for this account
                if acct_num:
                    tx_rows = df_tx[df_tx['Account Number'].astype(str) == acct_num]
                else:
                    # If account number missing, take all rows with empty account and later assign
                    tx_rows = df_tx[df_tx['Account Number'].astype(str).isin(['', 'nan'])]

                transactions = []
                running_balance = begin_bal
                for _, tx in tx_rows.iterrows():
                    deposit = money_to_float(tx.get('Deposits'))
                    withdrawal = money_to_float(tx.get('Withdrawals'))
                    # If file already has Running Balance as number, prefer it; else compute
                    rb = tx.get('Running Balance')
                    if pd.notna(rb) and str(rb) != '':
                        try:
                            running_balance = money_to_float(rb)
                        except Exception:
                            running_balance = running_balance + deposit - withdrawal
                    else:
                        running_balance = running_balance + deposit - withdrawal

                    transactions.append({
                        'date': str(tx.get('Date')) if pd.notna(tx.get('Date')) else '',
                        'description': str(tx.get('Description')) if pd.notna(tx.get('Description')) else '',
                        'deposit': deposit,
                        'withdrawal': withdrawal,
                        'running_balance': running_balance,
                        'check_number': '',
                        'category': ''
                    })

                accounts.append({
                    'account_number': acct_num,
                    'account_type': '',
                    'beginning_balance': begin_bal,
                    'ending_balance': end_bal,
                    'transactions': transactions,
                })

            # Metadata from first row
            if not df_summary.empty:
                first = df_summary.iloc[0]
                start_date, end_date = parse_period(first.get('Statement Period'))
                statements.append({
                    'metadata': {
                        'account_holder': str(first.get('Client Name')) if pd.notna(first.get('Client Name')) else '',
                        'bank_name': str(first.get('Bank Name')) if pd.notna(first.get('Bank Name')) else '',
                        'statement_period': {
                            'start_date': start_date,
                            'end_date': end_date,
                        },
                    },
                    'accounts': accounts,
                })
                found_any = True

    if found_any:
        return statements
    return []


def load_receipts():
    """Load receipt data from JSON files (structured output)."""
    output_dir = 'output/receipts'
    receipts = []
    if not os.path.exists(output_dir):
        return receipts
    for file in os.listdir(output_dir):
        if file.endswith('_receipt.json'):
            try:
                with open(os.path.join(output_dir, file), 'r') as f:
                    payload = json.load(f)
                    # Each file may contain a list of receipts
                    if isinstance(payload, list):
                        receipts.extend(payload)
                    elif isinstance(payload, dict):
                        receipts.append(payload)
            except Exception as e:
                print(f"Error reading receipt file {file}: {e}")
    return receipts


def load_invoices():
    """Load invoice data from JSON files (structured output)."""
    output_dir = 'output/invoices'
    invoices = []
    if not os.path.exists(output_dir):
        return invoices
    for file in os.listdir(output_dir):
        if file.endswith('_invoice.json'):
            try:
                with open(os.path.join(output_dir, file), 'r') as f:
                    payload = json.load(f)
                    # Each file may contain a list of invoices
                    if isinstance(payload, list):
                        invoices.extend(payload)
                    elif isinstance(payload, dict):
                        invoices.append(payload)
            except Exception as e:
                print(f"Error reading invoice file {file}: {e}")
    return invoices

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bank-statements')
def get_bank_statements():
    data = load_bank_statements()
    
    if data:
        try:
            # Prepare transaction data for visualization
            all_transactions = []
            for statement in data:
                for account in statement['accounts']:
                    for transaction in account['transactions']:
                        all_transactions.append({
                            'date': transaction['date'],
                            'account_number': account['account_number'],
                            'description': transaction['description'],
                            'deposit': transaction['deposit'],
                            'withdrawal': transaction['withdrawal'],
                            'running_balance': transaction['running_balance']
                        })
            
            df = pd.DataFrame(all_transactions)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date'])
            
            # Create monthly summary
            if not df.empty:
                monthly = df.groupby(df['date'].dt.strftime('%Y-%m')).agg({
                    'deposit': 'sum',
                    'withdrawal': 'sum'
                }).reset_index().rename(columns={'date': 'date'})
            else:
                monthly = pd.DataFrame(columns=['date', 'deposit', 'withdrawal'])
            
            # Create visualizations
            fig1 = px.line(monthly, x='date', 
                          y=['deposit', 'withdrawal'],
                          title='Monthly Transaction Summary')
            
            fig2 = go.Figure()
            if not df.empty:
                for account in pd.unique(df['account_number']):
                    account_data = df[df['account_number'] == account]
                    fig2.add_trace(go.Scatter(
                        x=account_data['date'],
                        y=account_data['running_balance'],
                        name=f'Account {account}',
                        mode='lines'
                    ))
            fig2.update_layout(title='Account Balances Over Time')
            
            return jsonify({
                'statements': data,
                'visualizations': {
                    'monthly_summary': json.loads(fig1.to_json()),
                    'balance_trends': json.loads(fig2.to_json())
                }
            })
            
        except Exception as e:
            print(f"Error processing data: {str(e)}")
            return jsonify({'error': str(e)})
    
    return jsonify({'error': 'No bank statement data found'})

@app.route('/api/receipts')
def get_receipts():
    receipts = load_receipts()
    if not receipts:
        return jsonify({'error': 'No receipt data found'})

    df = pd.DataFrame(receipts)
    # Normalize columns
    if 'merchant_name' not in df.columns:
        df['merchant_name'] = 'Unknown'
    if 'total' not in df.columns:
        df['total'] = 0.0
    if 'tax' not in df.columns:
        df['tax'] = 0.0
    if 'transaction_date' not in df.columns:
        df['transaction_date'] = ''

    # Coerce data types
    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0.0)
    df['tax'] = pd.to_numeric(df['tax'], errors='coerce').fillna(0.0)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')

    # Read filters
    merchant_q = request.args.get('merchant', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    min_total = request.args.get('min_total', '').strip()
    max_total = request.args.get('max_total', '').strip()

    filtered = df.copy()
    if merchant_q:
        filtered = filtered[filtered['merchant_name'].str.contains(merchant_q, case=False, na=False)]
    if start_date:
        try:
            sd = pd.to_datetime(start_date)
            filtered = filtered[filtered['transaction_date'] >= sd]
        except Exception:
            pass
    if end_date:
        try:
            ed = pd.to_datetime(end_date)
            filtered = filtered[filtered['transaction_date'] <= ed]
        except Exception:
            pass
    if min_total:
        try:
            mn = float(min_total)
            filtered = filtered[filtered['total'] >= mn]
        except Exception:
            pass
    if max_total:
        try:
            mx = float(max_total)
            filtered = filtered[filtered['total'] <= mx]
        except Exception:
            pass

    # Group by merchant
    if not filtered.empty:
        grouped = (
            filtered.groupby('merchant_name').agg(
                receipts_count=('merchant_name', 'size'),
                total_amount=('total', 'sum'),
                total_tax=('tax', 'sum'),
                avg_amount=('total', 'mean'),
            )
            .reset_index()
            .sort_values('total_amount', ascending=False)
        )
    else:
        grouped = pd.DataFrame(columns=['merchant_name', 'receipts_count', 'total_amount', 'total_tax', 'avg_amount'])

    # Visualization: bar chart of top merchants by total
    fig = px.bar(
        grouped.head(15), x='merchant_name', y='total_amount',
        title='Top Merchants by Total Spend', labels={'total_amount': 'Total ($)', 'merchant_name': 'Merchant'}
    )
    fig.update_layout(xaxis_tickangle=-30, height=400)

    # JSON outputs
    # Convert dates back to string for JSON
    filtered_out = filtered.copy()
    filtered_out['transaction_date'] = filtered_out['transaction_date'].dt.strftime('%Y-%m-%d')

    return jsonify({
        'receipts': filtered_out.to_dict('records'),
        'grouped': grouped.to_dict('records'),
        'visualization': json.loads(fig.to_json()),
        'filters_applied': {
            'merchant': merchant_q,
            'start_date': start_date,
            'end_date': end_date,
            'min_total': min_total,
            'max_total': max_total,
        }
    })

@app.route('/api/invoices')
def get_invoices():
    invoices = load_invoices()
    if invoices:
        # Create vendor summary visualization
        vendor_summary = pd.DataFrame(invoices)
        if 'vendor_name' not in vendor_summary.columns:
            vendor_summary['vendor_name'] = 'Unknown'
        # Coerce totals to numeric from strings like "$1,234.56"
        if 'invoice_total' in vendor_summary.columns:
            totals = vendor_summary['invoice_total']
            if totals.dtype == 'object':
                vendor_summary['invoice_total_value'] = pd.to_numeric(
                    totals.replace(r'[^0-9\.\-]', '', regex=True), errors='coerce'
                ).fillna(0.0)
            else:
                vendor_summary['invoice_total_value'] = pd.to_numeric(totals, errors='coerce').fillna(0.0)
        else:
            vendor_summary['invoice_total_value'] = 0.0

        fig = px.bar(
            vendor_summary, x='vendor_name', y='invoice_total_value',
            title='Invoice Amounts by Vendor'
        )
        
        return jsonify({
            'invoices': invoices,
            'visualization': json.loads(fig.to_json())
        })
    
    return jsonify({'error': 'No invoice data found'})

@app.route('/debug/bank-statements')
def debug_bank_statements():
    """Debug endpoint to check raw bank statement data"""
    statements = load_bank_statements()
    # Compute counts for quick sanity check
    total_accounts = 0
    total_transactions = 0
    sample_statement = None
    sample_account = None
    sample_transaction = None
    if statements:
        sample_statement = statements[0]
        if sample_statement.get('accounts'):
            sample_account = sample_statement['accounts'][0]
            total_accounts = sum(len(s.get('accounts', [])) for s in statements)
            if sample_account.get('transactions'):
                sample_transaction = sample_account['transactions'][0]
                total_transactions = sum(
                    len(a.get('transactions', []))
                    for s in statements for a in s.get('accounts', [])
                )

    return jsonify({
        'statements_count': len(statements),
        'accounts_count': total_accounts,
        'transactions_count': total_transactions,
        'sample_statement': sample_statement,
        'sample_account': sample_account,
        'sample_transaction': sample_transaction,
    })

@app.route('/debug/receipts')
def debug_receipts():
    """Debug endpoint to check raw receipts and file discovery."""
    output_dir = 'output/receipts'
    files = []
    try:
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith('_receipt.json')]
    except Exception as e:
        files = [f"<error listing files: {e}>"]

    receipts = load_receipts()
    merchants = {}
    date_min = None
    date_max = None
    for r in receipts:
        m = r.get('merchant_name') or 'Unknown'
        merchants[m] = merchants.get(m, 0) + 1
        try:
            d = pd.to_datetime(r.get('transaction_date'))
            if pd.notna(d):
                if date_min is None or d < date_min:
                    date_min = d
                if date_max is None or d > date_max:
                    date_max = d
        except Exception:
            pass

    sample_receipt = receipts[0] if receipts else None
    return jsonify({
        'files_found': files,
        'file_count': len(files),
        'receipt_count': len(receipts),
        'merchants_top': sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10],
        'date_range': {
            'min': date_min.strftime('%Y-%m-%d') if date_min is not None else '',
            'max': date_max.strftime('%Y-%m-%d') if date_max is not None else ''
        },
        'sample_receipt': sample_receipt,
    })

if __name__ == '__main__':
    app.run(debug=True)
