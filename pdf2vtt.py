import os

from extractor.data_loaders.pdf_loader import PDFLoader
from extractor.outputs.default_writer import DefaultWriter
from extractor.outputs.print_writer import PrintWriter
from extractor.outputs.fvtt_writer import FVTTWriter

from extractor.utils.config import get_config, get_cli_argparser
from extractor.utils.logger import get_logger

from extractor.data_loaders.textract_image_loader import TextractImageLoader
from extractor.data_loaders.pdf_loader import PDFLoader

from extractor.core.extractor import StatblockExtractor
from extractor.outputs.creature_printer import pretty_format_creature




# Get arguments
parser = get_cli_argparser()
args = parser.parse_args()

# Get config file
config = get_config(args, cli=True)

if not config.has_section("source"):
    config.add_section("source")
if args.authors:
    authors = []
    for a in args.authors:
        authors += [v.strip() for v in a.split(",")]
    config.set("source", "authors", ",".join(authors))
if args.url:
    config.set("source", "url", args.url)
if args.source:
    config.set("source", "title", args.source)


# Setup logger
logger = get_logger(args.debug, args.logs)

### Create Extractor
se = StatblockExtractor(config, logger)

### Register Input formats
se.register_data_loader(TextractImageLoader)
se.register_data_loader(PDFLoader)

### Register Output formats and select one
se.register_output_writer(DefaultWriter, append=not args.overwrite)
se.register_output_writer(PrintWriter, append=not args.overwrite)
se.register_output_writer(FVTTWriter, append=not args.overwrite)
output = True
if args.format:
    if args.format == 'none':
        output = False
    else:
        se.select_writer(args.format)
else:
    se.select_writer(FVTTWriter.get_name())

### Run over provided targets 
logger.info("Loading creatures from {}".format(args.target))

if args.pages:
    pages = [[int(p) for p in pages.split(",")] for pages in args.pages.split(";")]
else:
    pages = None

results = se.parse_multiple(args.target, pages=pages)
if not results:
    exit()

p_func = print

for source_name in results:
    source, errors = results[source_name]
    p_func("Found {} statblocks in {}".format(len(source.statblocks), source.name))

    if output:
        if args.output:
            outfile = args.output
        else:
            outfile = "{}.{}".format(os.path.basename(source.name).split('.')[0], se.writer.get_filetype())

        se.write_to_file(outfile, source, {0:source.statblocks})

    if args.print:
        for statblock in source.statblocks:
            p_func("\n" + pretty_format_creature(statblock) + "\n")


        

    