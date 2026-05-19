"""Model deployment classification for rule/policy evaluation context."""


def deployment_flags(model) -> tuple[str | None, bool]:
    """
    Map compliance model type to deployment label and external flag.

    Returns (deployment, is_external) used by rule engine context.
    """
    mapping = {
        "local_model": ("local", False),
        "external_api": ("external", True),
        "cloud_hosted": ("cloud", True),
        "open_source": ("local", False),
        "proprietary": ("cloud", True),
    }
    deployment, is_external = mapping.get(
        model.model_type, ("external", model.data_leaves_platform)
    )
    if model.data_leaves_platform:
        is_external = True
    return deployment, is_external
