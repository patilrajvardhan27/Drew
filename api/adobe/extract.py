import math

from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import (
    ExtractElementType,
)
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import (
    ExtractPDFParams,
)
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import (  # noqa: E501
    ExtractRenditionsElementType,
)
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.table_structure_type import (
    TableStructureType,
)
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult

from api.adobe.output import ExtractOutput
from api.adobe.streams import read_stream

PAGES_PER_TRANSACTION = 5


def extract_cost(pages: int) -> int:
    return max(1, math.ceil(pages / PAGES_PER_TRANSACTION))


def extract_job(pdf: bytes):
    def job(services: PDFServices) -> ExtractOutput:
        asset = services.upload(input_stream=pdf, mime_type=PDFServicesMediaType.PDF)
        params = ExtractPDFParams(
            elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
            elements_to_extract_renditions=[ExtractRenditionsElementType.TABLES],
            table_structure_type=TableStructureType.CSV,
        )
        location = services.submit(ExtractPDFJob(input_asset=asset, extract_pdf_params=params))
        result = services.get_job_result(location, ExtractPDFResult).get_result()
        resource = services.get_content(result.get_resource())
        return ExtractOutput.from_zip(read_stream(resource))

    return job
