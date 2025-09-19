# import libraries
import os
import json
import glob
from datetime import datetime
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv
import base64

# set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
load_dotenv()
endpoint = os.getenv("AZURE_DOC_ENDPOINT")
key = os.getenv("AZURE_DOC_KEY")


class DocumentBatchAnalyzer:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv("AZURE_DOC_ENDPOINT")
        self.key = os.getenv("AZURE_DOC_KEY")
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint, 
            credential=AzureKeyCredential(self.key)
        )
        
    def analyze_batch(self, input_dir, output_dir, document_type):
        """
        Analyze all documents of a specific type in a directory
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get all PDF files in input directory
        supported_formats = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif')
        files = []
        for format in supported_formats:
            files.extend(glob.glob(os.path.join(input_dir, f'*{format}')))
            
        results = {
            'succeeded': [],
            'failed': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for file_path in files:
            try:
                # Process file based on document type
                if document_type == "bankStatement":
                    result = self._analyze_bank_statement(file_path, output_dir)
                elif document_type == "receipt":
                    result = self._analyze_receipt(file_path, output_dir)
                elif document_type == "invoice":
                    result = self._analyze_invoice(file_path, output_dir)
                
                results['succeeded'].append({
                    'file': file_path,
                    'output': result
                })
                
            except Exception as e:
                results['failed'].append({
                    'file': file_path,
                    'error': str(e)
                })
                
        # Save batch results summary
        summary_path = os.path.join(output_dir, f'batch_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results

    def _analyze_bank_statement(self, file_path, output_dir):
        """Process bank statement and save results"""
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        
        with open(file_path, "rb") as file_stream:
            base64_data = base64.b64encode(file_stream.read()).decode("utf-8")
            poller = self.client.begin_analyze_document(
                "prebuilt-bankStatement.us", 
                analyze_request={"base64Source": base64_data}
            )
        result = poller.result()
        
        # Save raw analysis
        raw_output = os.path.join(output_dir, f"{base_filename}_raw.json")
        with open(raw_output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
            
        # Process and save structured data
        self._save_bank_statement_data(result, base_filename, output_dir)
        
        return {
            'raw_output': raw_output,
            'processed_files': {
                'summary': f"{base_filename}_summary.csv",
                'transactions': f"{base_filename}_transactions.csv"
            }
        }

    def _analyze_receipt(self, file_path, output_dir):
        """Process receipt and save results"""
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        
        with open(file_path, "rb") as file_stream:
            base64_data = base64.b64encode(file_stream.read()).decode("utf-8")
            poller = self.client.begin_analyze_document(
                "prebuilt-receipt",
                analyze_request={"base64Source": base64_data}
            )
        result = poller.result()
        
        # Save raw and processed results
        raw_output = os.path.join(output_dir, f"{base_filename}_raw.json")
        processed_output = os.path.join(output_dir, f"{base_filename}_processed.json")
        
        with open(raw_output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
            
        # Process and save structured data
        processed_data = self._process_receipt_data(result)
        with open(processed_output, 'w') as f:
            json.dump(processed_data, f, indent=2)
            
        return {
            'raw_output': raw_output,
            'processed_output': processed_output
        }

    def _analyze_invoice(self, file_path, output_dir):
        """Process invoice and save results"""
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        
        with open(file_path, "rb") as file_stream:
            base64_data = base64.b64encode(file_stream.read()).decode("utf-8")
            poller = self.client.begin_analyze_document(
                "prebuilt-invoice",
                analyze_request={"base64Source": base64_data}
            )
        result = poller.result()
        
        # Save raw and processed results
        raw_output = os.path.join(output_dir, f"{base_filename}_raw.json")
        processed_output = os.path.join(output_dir, f"{base_filename}_processed.json")
        
        with open(raw_output, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
            
        # Process and save structured data
        processed_data = self._process_invoice_data(result)
        with open(processed_output, 'w') as f:
            json.dump(processed_data, f, indent=2)
            
        return {
            'raw_output': raw_output,
            'processed_output': processed_output
        }
    

if __name__ == "__main__":
    analyzer = DocumentBatchAnalyzer()

    # Analyze batch of bank statements
    bank_results = analyzer.analyze_batch(
        input_dir="input/bank_statements",
        output_dir="output/bank_statements",
        document_type="bankStatement"
    )

    # Analyze batch of receipts
    receipt_results = analyzer.analyze_batch(
        input_dir="input/receipts",
        output_dir="output/receipts",
        document_type="receipt"
    )

    # # Analyze batch of invoices
    # invoice_results = analyzer.analyze_batch(
    #     input_dir="input/invoices",
    #     output_dir="output/invoices",
    #     document_type="invoice"
    # )