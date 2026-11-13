import math

from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.html_to_pdf_job import HTMLtoPDFJob
from adobe.pdfservices.operation.pdfjobs.params.html_to_pdf.html_to_pdf_params import (
    HTMLtoPDFParams,
)
from adobe.pdfservices.operation.pdfjobs.params.html_to_pdf.page_layout import PageLayout
from adobe.pdfservices.operation.pdfjobs.result.html_to_pdf_result import HTMLtoPDFResult

from api.adobe.streams import read_stream

PAGES_PER_TRANSACTION = 50


def html_to_pdf_cost(pages: int) -> int:
    return max(1, math.ceil(pages / PAGES_PER_TRANSACTION))


def html_to_pdf_job(html: str):
    def job(services: PDFServices) -> bytes:
        asset = services.upload(input_stream=html.encode("utf-8"), mime_type=PDFServicesMediaType.HTML)
        params = HTMLtoPDFParams(
            page_layout=PageLayout(page_height=11, page_width=8.5),
            include_header_footer=False,
        )
        location = services.submit(HTMLtoPDFJob(input_asset=asset, html_to_pdf_params=params))
        result = services.get_job_result(location, HTMLtoPDFResult).get_result()
        return read_stream(services.get_content(result.get_asset()))

    return job
