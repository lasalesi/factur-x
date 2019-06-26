# -*- coding: utf-8 -*-
# Copyright (C) 2019 lasalesi and contributors

import sys
#from facturx import get_facturx_xml_from_pdf
from PyPDF4 import PdfFileReader
import logging
from lxml import etree

FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('factur-x')
logger.setLevel(logging.DEBUG)  # options: DEBUG, INFO

#FACTURX_FILENAME = 'zugferd-invoice.xml' # > [ERROR] No valid XML file found in the PDF
#FACTURX_FILENAME = 'factur-x.xml'   # [DEBUG] found filename=zugferd-invoice.xml, [INFO] Returning an XML file False
FACTURX_FILENAME = ['factur-x.xml', 'zugferd-invoice.xml', 'ZUGFeRD-invoice.xml']

def get_facturx_xml_from_pdf(pdf_invoice, check_xsd=True):
    if not pdf_invoice:
        raise ValueError('Missing pdf_invoice argument')
    if not isinstance(check_xsd, bool):
        raise ValueError('Missing pdf_invoice argument')
    if isinstance(pdf_invoice, str):
        pdf_file = BytesIO(pdf_invoice)
    elif isinstance(pdf_invoice, file):
        pdf_file = pdf_invoice
    else:
        raise TypeError(
            "The first argument of the method get_facturx_xml_from_pdf must "
            "be either a string or a file (it is a %s)." % type(pdf_invoice))
    xml_string = xml_filename = False
    pdf = PdfFileReader(pdf_file)
    pdf_root = pdf.trailer['/Root']  # = Catalog
    logger.debug('pdf_root=%s', pdf_root)
    catalog_name = _get_dict_entry(pdf_root, '/Names')
    if not catalog_name:
        logger.info('No Names entry in Catalog')
        return (None, None)
    embeddedfiles_node = _get_dict_entry(catalog_name, '/EmbeddedFiles')
    if not embeddedfiles_node:
        logger.info('No EmbeddedFiles entry in the /Names of the Catalog')
        return (None, None)
    embeddedfiles = _get_embeddedfiles(embeddedfiles_node)
    logger.debug('embeddedfiles=%s', embeddedfiles)
    if not embeddedfiles:
        return (None, None)
    embeddedfiles_by_two = list(zip(embeddedfiles, embeddedfiles[1:]))[::2]
    logger.debug('embeddedfiles_by_two=%s', embeddedfiles_by_two)
    if True: #try:
        for (filename, file_obj) in embeddedfiles_by_two:
            logger.debug('found filename=%s', filename)
            if filename in (FACTURX_FILENAME):
                xml_file_dict = file_obj.getObject()
                logger.debug('xml_file_dict=%s', xml_file_dict)
                tmp_xml_string = xml_file_dict['/EF']['/F'].getData()
                xml_root = etree.fromstring(tmp_xml_string)
                logger.info(
                    'A valid XML file %s has been found in the PDF file',
                    filename)
                if check_xsd:
                    check_facturx_xsd(xml_root)
                    xml_string = tmp_xml_string
                    xml_filename = filename
                else:
                    xml_string = tmp_xml_string
                    xml_filename = filename
                break
            else:
                logger.debug('filename not in expected file names list')
    #except:
    #    logger.error('No valid XML file found in the PDF')
    #    return (None, None)
    logger.info('Returning an XML file %s', xml_filename)
    logger.debug('Content of the XML file: %s', xml_string)
    return (xml_filename, xml_string)

def _get_dict_entry(node, entry):
    if not isinstance(node, dict):
        raise ValueError('The node must be a dict')
    dict_entry = node.get(entry)
    if isinstance(dict_entry, dict):
        return dict_entry
    elif isinstance(dict_entry, IndirectObject):
        res_dict_entry = dict_entry.getObject()
        if isinstance(res_dict_entry, dict):
            return res_dict_entry
        else:
            return False
    else:
        return False

def _get_embeddedfiles(embeddedfiles_node):
    if not isinstance(embeddedfiles_node, dict):
        raise ValueError('The EmbeddedFiles node must be a dict')
    res = []
    if '/Names' in embeddedfiles_node:
        if not isinstance(embeddedfiles_node['/Names'], list):
            logger.error(
                'The /Names entry of the EmbeddedFiles name tree must '
                'be an array')
            return False
        res = embeddedfiles_node['/Names']
    elif '/Kids' in embeddedfiles_node:
        kids_node = embeddedfiles_node['/Kids']
        parse_result = _parse_embeddedfiles_kids_node(kids_node, 1, res)
        if parse_result is False:
            return False
    else:
        logger.error(
            'The EmbeddedFiles name tree should have either a /Names '
            'or a /Kids entry')
        return False
    if len(res) % 2 != 0:
        logger.error(
            'The EmbeddedFiles name tree should point to an even number of '
            'elements')
        return False
    return res
    

# ***** main ****
if len(sys.argv) < 2:
    print("Please provide the pdf file name as first command line argument")
    sys.exit()
    
pdf_filename = sys.argv[1]
    
check_xsd = False

pdf_file = open(pdf_filename, 'rb')

(xml_filename, xml_string) = get_facturx_xml_from_pdf(
            pdf_file, check_xsd=check_xsd)
        
print(xml_filename)
