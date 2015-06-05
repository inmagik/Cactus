from cactus.page import Page
import yaml

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
            self.build_path = self.source_path

    def is_html(self):
        return urlparse.urlparse(self.source_path).path.endswith('.html')

    def is_index(self):
        return urlparse.urlparse(self.compiled_path).path.endswith('index.html')