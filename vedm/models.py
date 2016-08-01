import logging

from django.db import models
from django.db import transaction

import vedm.util.cook


class Document(models.Model):
    '''A general document model.'''

    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField()

    date_created = models.DateField()
    date_updated = models.DateField()

    subtitle = models.TextField()
    ingress = models.TextField()
    body = models.TextField()

    parent_object = models.ForeignKey('self', related_name='children',
                                      null=True)

    model_instance_name = ('document', 'documents')
    cooked = (ingress, body)

    class Meta():
        ordering = ['date_created', 'title']

    @classmethod
    def create_en_masse(cls, raws):
        with transaction.atomic():
            by_pk = dict()

            for item in raws:
                new = cls.create(**item)
                by_pk[new.pk] = item

            # Add parents, which we presume are now saved.
            for pk, item in by_pk.items():
                sluggable = item.get('parent_object')
                if sluggable:
                    slug = vedm.util.cook.slugify(sluggable)
                    try:
                        parent = cls.objects.get(slug=slug)
                    except cls.DoesNotExist:
                        s = 'Stated parent "{}" not found.'
                        logging.error(s.format(sluggable))
                        continue
                    child = cls.objects.get(pk=pk)
                    child.parent_object = parent
                    child.save()

    @classmethod
    def create(cls, title='', parent_object=None, tags=None, **kwargs):
        '''Ignore parent object, because it may not be saved yet.'''

        slug = vedm.util.cook.slugify(title)
        vedm.util.cook.all_md(cls, kwargs)
        new = cls.objects.create(title=title, slug=slug, **kwargs)
        if tags:
            new.tags.set(*tags)
        return new
