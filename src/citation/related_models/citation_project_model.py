from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from researchhub_access_group.constants import ADMIN, EDITOR, VIEWER
from researchhub_access_group.related_models.permission_model import Permission
from user.models import Organization
from utils.models import DefaultAuthenticatedModel


class CitationProject(DefaultAuthenticatedModel):

    """--- MODEL FIELDS ---"""

    is_public = models.BooleanField(
        blank=True,
        default=True,
        null=False,
    )
    slug = models.SlugField(
        max_length=1024,
        blank=True,
        help_text="Slug is automatically generated on a signal, so it is not needed in a form",
    )
    parent_names = models.JSONField(
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    permissions = GenericRelation(
        Permission,
        related_name="citation_projects",
        related_query_name="citation_project",
    )
    project_name = models.CharField(
        max_length=1024,
    )
    organization = models.ForeignKey(
        Organization,
        related_name="citation_projects",
        on_delete=models.CASCADE,
    )

    """--- METHODS ---"""

    def get_parent_name(self, project, names=[], slugs=[]):
        names.append(project.project_name)
        slugs.append(project.slug)
        if not project.parent:
            names.reverse()
            slugs.reverse()
            return {"names": names, "slugs": slugs}
        else:
            return self.get_parent_name(project.parent, names, slugs)

    def add_editors(self, editor_ids=[]):
        for editor_id in editor_ids:
            editor_exists = self.permissions.has_editor_user(editor_id)
            if not editor_exists:
                self.permissions.create(access_type=EDITOR, user_id=editor_id)
        return True

    def add_viewers(self, viewer_ids=[]):
        for viewer_id in viewer_ids:
            viewer_exists = self.permissions.has_viewer_user(viewer_id)
            if not viewer_exists:
                self.permissions.create(access_type=VIEWER, user_id=viewer_id)
        return True

    def get_is_user_admin(self, user):
        if self.get_user_has_access(user):
            return self.permissions.has_admin_user(user)

    def get_user_has_access(self, user):
        org_has_user = self.organization.org_has_user(user)
        if not org_has_user:
            return False

        if self.is_public:
            return True
        else:
            return self.permissions.has_user(user)

    def remove_editors(self, editor_ids):
        for editor_id in editor_ids:
            self.permissions.filter(access_type=EDITOR, user=editor_id).all().delete()
        return True

    def remove_viewers(self, viewer_ids):
        for viewer_id in viewer_ids:
            self.permissions.filter(
                access_type=VIEWER, user_id=viewer_id
            ).all().delete()
        return True

    def set_creator_as_admin(self):
        self.permissions.create(access_type=ADMIN, user=self.created_by)
        return True
