"""Profile factory module."""
import typing as t
import logging

from attrs import define, field

from .core import Profile

logger = logging.getLogger(__name__)


@define
class ProfileFactory:
    """
    Profile factory class.
    """

    """Profile registry."""
    registry: t.Dict[str, Profile] = field(factory=dict)

    def register(
        self,
        identifier: str,
    ) -> t.Callable:
        """
        Register a profile class.

        Args:
            identifier: Profile identifier.
        
        Returns:
            Decorator function.
        """

        def inner_wrapper(wrapped_class: Profile) -> t.Callable:
            logger.info("Registering profile %s", identifier)
            if identifier in self.registry:
                logger.warning(  # pragma: no cover
                    "Profile %s already exists. Will replace it",
                    identifier,
                )
            self.registry[identifier] = wrapped_class
            return wrapped_class

        return inner_wrapper

    def create(self, identifier: str, **kwargs) -> Profile:
        """
        Create a profile instance.

        Args:
            identifier: Profile identifier.

        Returns:
            Profile instance.
        """
        if identifier not in self.registry:
            logger.fatal("Profile %s does not exist in the registry", identifier)
            raise ValueError(f"Profile {identifier} does not exist in the registry")

        logger.debug("Creating profile %s", identifier)
        profile_cls = self.registry[identifier]
        profile = profile_cls(**kwargs)
        return profile


factory = ProfileFactory()
