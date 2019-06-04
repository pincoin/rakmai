import logging

from .models import Board


class BoardContextMixin(object):
    logger = logging.getLogger(__name__)

    def dispatch(self, *args, **kwargs):
        self.board = Board.objects.get(slug=self.kwargs.get('slug'))

        self.block_size = self.board.block_size
        self.chunk_size = self.board.chunk_size

        return super(BoardContextMixin, self).dispatch(*args, **kwargs)
