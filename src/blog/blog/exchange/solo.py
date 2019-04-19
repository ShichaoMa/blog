from apistellar import Solo

from blog.blog.article.article_exporter import ArticleExporter


class Exchange(Solo):
    """
    将网页转换pdf
    """
    def __init__(self, input_path, output_path, **kwargs):
        self.input_path = input_path
        self.output_path = output_path
        super(Exchange, self).__init__(**kwargs)

    async def setup(self):
        """
        初始化
        :return:
        """

    async def run(self):
        """
        业务逻辑
        :return:
        """
        with open(self.input_path) as f:
            await ArticleExporter.save_as_pdf(f.read(), self.output_path)

    async def teardown(self):
        """
        回收资源
        :return:
        """

    @classmethod
    def enrich_parser(cls, sub_parser):
        """
        自定义命令行参数，若定义了，则可通过__init__获取
        注意在__init__中使用kwargs来保留其它参数，并调用父类的__init__
        :param sub_parser:
        :return:
        """
        sub_parser.add_argument("-i", "--input-path")
        sub_parser.add_argument("-o", "--output-path")


