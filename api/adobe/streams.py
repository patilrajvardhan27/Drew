from adobe.pdfservices.operation.io.stream_asset import StreamAsset


def read_stream(asset: StreamAsset) -> bytes:
    stream = asset.get_input_stream()
    return stream if isinstance(stream, bytes) else stream.read()
