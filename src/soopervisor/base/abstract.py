import abc

from pydantic import BaseModel


class AbstractBaseModel(BaseModel):
    class Config:
        extra = 'forbid'

    # computed fields (fields whose value depends on other fields) must
    # properly identifier with this marker:
    # COMPUTED FIELDS

    @abc.abstractmethod
    def render(self):
        """
        **Must be called in the last line of __init__**
        Some values are computed and others have to be modified before the
        configuration can be used, all these should happen in the render
        method. If a nested model require data from its parent, it should
        add them as extra arguments to this method.

        Since this process only happens during initialization, config objects
        should not be updated after initialized.
        """
        pass

    # helper methods must have a leading underscore


class AbstractConfig(AbstractBaseModel):
    """
    Defines the abstract pydantic model that other configuration objects must
    implement. Config objects are usually initialized using the
    ``from_path`` class method, which reads the YAML soopervisor.yaml file.

    During initialization config objects only validate field values, but do not
    verify if these values are meaningful. e.g. if a field requires an absolute
    path, we verify the format, but not that the path actually exists. These
    process only happens when using ``from_path``.

    We compared pydantic and traitlets, ended up using pydantic as if offers
    a cleaner API. However, there are still a few nuances. Our models require
    processing some of the values submitted by the user, for example, if they
    say the project_root is "." we convert that to an absolute path, sometimes
    some values are computed, for example, the project_name is assigned to
    the name of the project's root folder.

    pydantic's API does not allow for private attributes (i.e. if you do
    self._{something} you get an error). This is inconvenient for computed
    values since (e.g. project_name). The best solution we found is to simply
    declared them as fields but do not document them. See ScriptConfig for
    an example
    """
    @abc.abstractclassmethod
    def from_project(cls, project_root):
        """
        Public API to interface with other modules, it loads the YAML file
        from soopervisor.yaml, renders the model and validates the project
        """
        # put the export logic here as well
        pass
