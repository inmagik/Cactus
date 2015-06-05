from cactus.page import Page
import os
import urlparse
import yaml
from django.template import Template, Context
import re

BLOCK_RE = re.compile(r'{%\s*block\s*(\w+)\s*%}')
NAMED_BLOCK_RE = r'{%%\s*block\s*%s\s*%%}'  # Accepts string formatting
ENDBLOCK_RE = re.compile(r'{%\s*endblock\s*(?:\w+\s*)?%}')


def get_block_source(template_source, block_name):
    """
    Given a template's source code, and the name of a defined block tag,
    returns the source inside the block tag.
    """
    # Find the open block for the given name
    match = re.search(NAMED_BLOCK_RE % (block_name,), template_source)
    if match is None:
        raise ValueError(u'Template block {n} not found'.format(n=block_name))
    end = inner_start = start = match.end()
    end_width = 0
    while True:
        # Set ``end`` current end to just out side the previous end block
        end += end_width
        # Find the next end block
        match = re.search(ENDBLOCK_RE, template_source[end:])
        # Set ``end`` to just inside the next end block
        end += match.start()
        # Get the width of the end block, in case of another iteration
        end_width = match.end() - match.start()
        # Search for any open blocks between any previously found open blocks,
        # and the current ``end``
        nested = re.search(BLOCK_RE, template_source[inner_start:end])
        if nested is None:
            # Nothing found, so we have the correct end block
            break
        else:
            # Nested open block found, so set our nested search cursor to just
            # past the inner open block that was found, and continue iteration
            inner_start += nested.end()
    # Return the value between our ``start`` and final ``end`` locations
    return start #template_source[start:end]

class YamlPage(Page):
    
    def __init__(self, site, source_path):
        self.site = site

        # The path where this element should be linked in "base" pages
        self.source_path = source_path

        pieces = self.source_path.split(".")
        pieces = [p for p in pieces if p != "yaml"]
        self.compiled_path = ".".join(pieces)


        # The URL where this element should be linked in "base" pages
        self.link_url = '/{0}'.format(self.compiled_path)

        #TODO: check and test
        if self.site.prettify_urls:
            # The URL where this element should be linked in "built" pages
            if self.is_html():
                if self.is_index():
                    self.final_url = self.link_url.rsplit('index.html', 1)[0]
                else:
                    self.final_url = '{0}/'.format(self.link_url.rsplit('.html', 1)[0])
            else:
                self.final_url = self.link_url

            # The path where this element should be built to
            if not self.is_html() or self.source_path.endswith('index.html'):
                self.build_path = self.source_path
            else:
                self.build_path = '{0}/{1}'.format(self.source_path.rsplit('.html', 1)[0], 'index.html')
        else:
            self.final_url = self.link_url
            self.build_path = self.compiled_path

    def is_html(self):
        return urlparse.urlparse(self.compiled_path).path.endswith('.html')

    def is_index(self):
        return urlparse.urlparse(self.compiled_path).path.endswith('index.html')

    @property
    def full_source_path(self):
        return os.path.join(self.site.path, 'yaml_pages', self.source_path)

    def yaml_data(self):
        with open(self.full_source_path) as f:
            data = yaml.load(f)

        return data

    def context(self, data=None, extra=None):
        """
        The page context.
        """
        if extra is None:
            extra = {}

        context = {'__CACTUS_CURRENT_PAGE__': self,}
        
        page_context, data = self.parse_context(data or self.data())

        context.update(self.site.context())
        context.update(extra)
        context.update(page_context)

        return Context(context)


    def render_piece(self, theme, context, block_data):

        template = block_data['tpl']
        full_template_path = os.path.join(self.site.themes_path, theme, 'templates', template)
        
        ctx = Context(context)
        if 'ctx' in block_data:
            ctx.update(block_data['ctx'])

        with open(full_template_path) as f:
            tpl = f.read()

        return Template(tpl).render(ctx)


    def render(self):
        """
        Takes the template data with context and renders it to the final output file.
        """
        yaml_data = self.yaml_data()
        
        template = yaml_data['tpl']
        theme = self.site.config.get('theme', None)

        if theme:
            full_template_path = os.path.join(self.site.themes_path, theme, 'templates', template)

        else:
            full_template_path = os.path.join(self.site.template_path, template)            
        
        if theme:
            template = theme + "/" + template

        
        ctx = yaml_data.get('ctx', {})
        context = self.context(extra=ctx)

        with open(full_template_path) as t:
            data = t.read()

        # This is not very nice, but we already used the header context in the
        # page context, so we don't need it anymore.
        #page_context, data = self.parse_context(data)


        context, data = self.site.plugin_manager.preBuildPage(
            self.site, self, context, data)

        
        if 'blocks' in yaml_data:
            for block in yaml_data['blocks']:
                block_start =  get_block_source(data, block)
                
                print block, block_start
                for component in yaml_data['blocks'][block]:
                    

                    piece = self.render_piece(theme, context, component).encode('utf-8')
                    data = data[:block_start] + piece + data[block_start:]
                    block_start = block_start + len(piece)




        return Template(data).render(context)

    

