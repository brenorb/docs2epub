from docs2epub.cli import _build_parser


def test_cli_keeps_images_by_default():
  args = _build_parser().parse_args(["https://example.com/docs", "book.epub"])
  assert args.keep_images is True


def test_cli_allows_disabling_images():
  args = _build_parser().parse_args(["https://example.com/docs", "book.epub", "--no-images"])
  assert args.keep_images is False
