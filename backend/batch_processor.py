import os
import json
import glob
from datetime import datetime
from typing import Dict, List
from doc_intel_quickstart import analyze_bank_statement, analyze_receipt, analyze_invoice


class DocumentBatchProcessor:
    def __init__(self, input_dir: str, output_dir: str):
        """Initialize batch processor with input and output directories"""
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.supported_formats = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif')
        
    def process_batch(self, document_type: str) -> Dict:
        """Process all documents of a specific type"""
        type_output_dir = os.path.join(self.output_dir, document_type)
        os.makedirs(type_output_dir, exist_ok=True)
        
        files = []
        for ext in self.supported_formats:
            files.extend(glob.glob(os.path.join(self.input_dir, document_type, f'*{ext}')))
        
        results = {
            'processed': [],
            'failed': [],
            'timestamp': datetime.now().isoformat()
        }
        
        for file_path in files:
            try:
                # Process based on document type
                if document_type == 'bank_statements':
                    output_file = analyze_bank_statement(
                        input_file=file_path,
                        output_dir=type_output_dir
                    )
                elif document_type == 'receipts':
                    output_file = analyze_receipt(
                        input_file=file_path,
                        output_dir=type_output_dir
                    )
                elif document_type == 'invoices':
                    output_file = analyze_invoice(
                        input_file=file_path,
                        output_dir=type_output_dir
                    )
                
                results['processed'].append({
                    'input_file': file_path,
                    'output_file': output_file,
                    'status': 'success'
                })
                
            except Exception as e:
                results['failed'].append({
                    'file': file_path,
                    'error': str(e)
                })
        
        # Save batch summary
        summary_file = os.path.join(
            type_output_dir, 
            f'batch_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
            
        return results

if __name__ == "__main__":
    # Initialize processor
    processor = DocumentBatchProcessor(
        input_dir="input",
        output_dir="output"
    )
    
    # Process each document type
    for doc_type in ['bank_statements', 'receipts', 'invoices']:
        print(f"\nProcessing {doc_type}...")
        results = processor.process_batch(doc_type)
        print(f"Processed: {len(results['processed'])} files")
        print(f"Failed: {len(results['failed'])} files")