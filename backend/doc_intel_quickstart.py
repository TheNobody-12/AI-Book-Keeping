# import libraries
import os
import csv
from datetime import datetime
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv
import base64
import json

# set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
load_dotenv()
endpoint = os.getenv("AZURE_DOC_ENDPOINT")
key = os.getenv("AZURE_DOC_KEY")

# helper functions

def get_words(page, line):
    result = []
    for word in page.words:
        if _in_span(word, line.spans):
            result.append(word)
    return result


def _in_span(word, spans):
    for span in spans:
        if word.span.offset >= span.offset and (
            word.span.offset + word.span.length
        ) <= (span.offset + span.length):
            return True
    return False

def analyze_bank_statement(input_file=None, output_dir=None):
    """Analyze bank statement with configurable input/output"""
    filepath = input_file or "07312025_SScotiabank.pdf"
    output_dir = output_dir or "output"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    # Read and process the PDF
    with open(filepath, "rb") as file_stream:
        base64_data = base64.b64encode(file_stream.read()).decode("utf-8")
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-bankStatement.us", analyze_request={"base64Source": base64_data}
        )
    bankstatements = poller.result()
    
    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    
    # Create structured data
    statement_data = []
    
    for statement in bankstatements.documents:
        statement_info = {
            "metadata": {
                "account_holder": statement.fields.get("AccountHolderName", {}).value_string if statement.fields.get("AccountHolderName") else "",
                "bank_name": statement.fields.get("BankName", {}).value_string if statement.fields.get("BankName") else "",
                "statement_period": {
                    "start_date": str(statement.fields.get("StatementStartDate").value_date) if statement.fields.get("StatementStartDate") else "",
                    "end_date": str(statement.fields.get("StatementEndDate").value_date) if statement.fields.get("StatementEndDate") else ""
                }
            },
            "accounts": []
        }
        
        accounts = statement.fields.get("Accounts", {}).value_array if statement.fields.get("Accounts") else []
        for account in accounts:
            account_info = {
                "account_number": account.value_object.get("AccountNumber", {}).value_string if account.value_object.get("AccountNumber") else "",
                "account_type": account.value_object.get("AccountType", {}).value_string if account.value_object.get("AccountType") else "",
                "beginning_balance": account.value_object.get("BeginningBalance", {}).value_number if account.value_object.get("BeginningBalance") else 0.0,
                "ending_balance": account.value_object.get("EndingBalance", {}).value_number if account.value_object.get("EndingBalance") else 0.0,
                "transactions": []
            }
            
            transactions = account.value_object.get("Transactions", {}).value_array if account.value_object.get("Transactions") else []
            running_balance = account_info["beginning_balance"]
            
            for transaction in transactions:
                deposit = transaction.value_object.get("DepositAmount", {}).value_number if transaction.value_object.get("DepositAmount") else 0.0
                withdrawal = transaction.value_object.get("WithdrawalAmount", {}).value_number if transaction.value_object.get("WithdrawalAmount") else 0.0
                running_balance += deposit - withdrawal
                
                transaction_info = {
                    "date": str(transaction.value_object.get("Date", {}).value_date) if transaction.value_object.get("Date") else "",
                    "description": transaction.value_object.get("Description", {}).value_string if transaction.value_object.get("Description") else "",
                    "deposit": deposit,
                    "withdrawal": withdrawal,
                    "running_balance": running_balance,
                    "check_number": transaction.value_object.get("CheckNumber", {}).value_string if transaction.value_object.get("CheckNumber") else "",
                    "category": transaction.value_object.get("Category", {}).value_string if transaction.value_object.get("Category") else ""
                }
                account_info["transactions"].append(transaction_info)
            
            statement_info["accounts"].append(account_info)
        
        statement_data.append(statement_info)
    
    # Save to JSON file
    results_file = os.path.join(output_dir, f"{base_filename}_bank_statement.json")
    with open(results_file, 'w') as f:
        json.dump(statement_data, f, indent=2)
    
    print(f"Created bank statement analysis file: {results_file}")
    print("--------------------------------------")
    return results_file

def analyze_receipt(input_file=None, output_dir=None):
    """Analyze receipt with configurable input/output"""
    output_dir = output_dir or "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    if input_file:
        # Process local file
        with open(input_file, "rb") as file_stream:
            base64_data = base64.b64encode(file_stream.read()).decode("utf-8")
            poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-receipt", analyze_request={"base64Source": base64_data}
            )
    else:
        # Use sample receipt URL as fallback
        receiptUrl = "https://raw.githubusercontent.com/Azure/azure-sdk-for-python/main/sdk/formrecognizer/azure-ai-formrecognizer/tests/sample_forms/receipt/contoso-receipt.png"
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-receipt", AnalyzeDocumentRequest(url_source=receiptUrl)
        )
    
    receipts = poller.result()
    base_filename = os.path.splitext(os.path.basename(input_file))[0] if input_file else "sample_receipt"
    
    # Save results to JSON file
    results_file = os.path.join(output_dir, f"{base_filename}_receipt.json")
    receipt_data = []
    
    for idx, receipt in enumerate(receipts.documents):
        receipt_info = {
            "receipt_number": idx + 1,
            "type": receipt.doc_type if receipt.doc_type else "",
            "merchant_name": receipt.fields.get("MerchantName", {}).value_string if receipt.fields.get("MerchantName") else "",
            "transaction_date": str(receipt.fields.get("TransactionDate", {}).value_date) if receipt.fields.get("TransactionDate") else "",
            "items": [],
            "subtotal": receipt.fields.get("Subtotal", {}).value_currency.amount if receipt.fields.get("Subtotal") else 0.0,
            "tax": receipt.fields.get("TotalTax", {}).value_currency.amount if receipt.fields.get("TotalTax") else 0.0,
            "tip": receipt.fields.get("Tip", {}).value_currency.amount if receipt.fields.get("Tip") else 0.0,
            "total": receipt.fields.get("Total", {}).value_currency.amount if receipt.fields.get("Total") else 0.0
        }
        
        if receipt.fields.get("Items"):
            for item in receipt.fields.get("Items").value_array:
                item_info = {
                    "description": item.value_object.get("Description", {}).value_string if item.value_object.get("Description") else "",
                    "quantity": item.value_object.get("Quantity", {}).value_number if item.value_object.get("Quantity") else 0,
                    "price": item.value_object.get("Price", {}).value_currency.amount if item.value_object.get("Price") else 0.0,
                    "total_price": item.value_object.get("TotalPrice", {}).value_currency.amount if item.value_object.get("TotalPrice") else 0.0
                }
                receipt_info["items"].append(item_info)
        
        receipt_data.append(receipt_info)
    
    with open(results_file, 'w') as f:
        json.dump(receipt_data, f, indent=2)
    
    print(f"Created receipt analysis file: {results_file}")
    print("--------------------------------------")
    return results_file

def analyze_invoice(input_file=None, output_dir=None):
    """Analyze invoice with configurable input/output"""
    output_dir = output_dir or "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    if input_file:
        # Process local file
        with open(input_file, "rb") as file_stream:
            base64_data = base64.b64encode(file_stream.read()).decode("utf-8")
            poller = document_intelligence_client.begin_analyze_document(
                "prebuilt-invoice", analyze_request={"base64Source": base64_data}
            )
    else:
        # Use sample invoice URL as fallback
        invoiceUrl = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-invoice.pdf"
        poller = document_intelligence_client.begin_analyze_document(
            "prebuilt-invoice", AnalyzeDocumentRequest(url_source=invoiceUrl)
        )
    
    invoices = poller.result()
    base_filename = os.path.splitext(os.path.basename(input_file))[0] if input_file else "sample_invoice"
    
    # Save results to JSON file
    results_file = os.path.join(output_dir, f"{base_filename}_invoice.json")
    invoice_data = []
    
    if invoices.documents:
        for idx, invoice in enumerate(invoices.documents):
            invoice_info = {
                "invoice_number": idx + 1,
                "vendor_name": invoice.fields.get("VendorName", {}).get('content') if invoice.fields.get("VendorName") else "",
                "vendor_address": invoice.fields.get("VendorAddress", {}).get('content') if invoice.fields.get("VendorAddress") else "",
                "customer_name": invoice.fields.get("CustomerName", {}).get('content') if invoice.fields.get("CustomerName") else "",
                "invoice_id": invoice.fields.get("InvoiceId", {}).get('content') if invoice.fields.get("InvoiceId") else "",
                "invoice_date": invoice.fields.get("InvoiceDate", {}).get('content') if invoice.fields.get("InvoiceDate") else "",
                "due_date": invoice.fields.get("DueDate", {}).get('content') if invoice.fields.get("DueDate") else "",
                "items": [],
                "subtotal": invoice.fields.get("SubTotal", {}).get('content') if invoice.fields.get("SubTotal") else "",
                "total_tax": invoice.fields.get("TotalTax", {}).get('content') if invoice.fields.get("TotalTax") else "",
                "invoice_total": invoice.fields.get("InvoiceTotal", {}).get('content') if invoice.fields.get("InvoiceTotal") else ""
            }
            
            if invoice.fields.get("Items"):
                for item in invoice.fields.get("Items").get("valueArray"):
                    item_info = {
                        "description": item.get("valueObject", {}).get("Description", {}).get('content', ""),
                        "quantity": item.get("valueObject", {}).get("Quantity", {}).get('content', ""),
                        "unit_price": item.get("valueObject", {}).get("UnitPrice", {}).get('content', ""),
                        "amount": item.get("valueObject", {}).get("Amount", {}).get('content', "")
                    }
                    invoice_info["items"].append(item_info)
            
            invoice_data.append(invoice_info)
    
    with open(results_file, 'w') as f:
        json.dump(invoice_data, f, indent=2)
    
    print(f"Created invoice analysis file: {results_file}")
    print("--------------------------------------")
    return results_file

def analyze_layout():
    # sample document
    formUrl = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-layout.pdf"

    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-layout", AnalyzeDocumentRequest(url_source=formUrl
    ))

    result: AnalyzeResult = poller.result()

    if result.styles and any([style.is_handwritten for style in result.styles]):
        print("Document contains handwritten content")
    else:
        print("Document does not contain handwritten content")

    for page in result.pages:
        print(f"----Analyzing layout from page #{page.page_number}----")
        print(
            f"Page has width: {page.width} and height: {page.height}, measured with unit: {page.unit}"
        )

        if page.lines:
            for line_idx, line in enumerate(page.lines):
                words = get_words(page, line)
                print(
                    f"...Line # {line_idx} has word count {len(words)} and text '{line.content}' "
                    f"within bounding polygon '{line.polygon}'"
                )

                for word in words:
                    print(
                        f"......Word '{word.content}' has a confidence of {word.confidence}"
                    )

        if page.selection_marks:
            for selection_mark in page.selection_marks:
                print(
                    f"Selection mark is '{selection_mark.state}' within bounding polygon "
                    f"'{selection_mark.polygon}' and has a confidence of {selection_mark.confidence}"
                )

    if result.tables:
        for table_idx, table in enumerate(result.tables):
            print(
                f"Table # {table_idx} has {table.row_count} rows and "
                f"{table.column_count} columns"
            )
            if table.bounding_regions:
                for region in table.bounding_regions:
                    print(
                        f"Table # {table_idx} location on page: {region.page_number} is {region.polygon}"
                    )
            for cell in table.cells:
                print(
                    f"...Cell[{cell.row_index}][{cell.column_index}] has text '{cell.content}'"
                )
                if cell.bounding_regions:
                    for region in cell.bounding_regions:
                        print(
                            f"...content on page {region.page_number} is within bounding polygon '{region.polygon}'"
                        )

    print("----------------------------------------")


if __name__ == "__main__":
    analyze_bank_statement()