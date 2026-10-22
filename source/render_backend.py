"""Choose an offscreen VTK context supported by the current platform."""
import os
import sys

def create_render_window(vtk):
    backend = os.environ.get("ARX_RENDER_BACKEND", "auto").lower()
    if backend not in ("auto", "native", "egl", "osmesa"):
        raise ValueError("ARX_RENDER_BACKEND must be auto, native, egl, or osmesa")
    if backend == "auto":
        backend = "egl" if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and hasattr(vtk, "vtkEGLRenderWindow") else "native"
    name = {"native": "vtkRenderWindow", "egl": "vtkEGLRenderWindow",
            "osmesa": "vtkOSOpenGLRenderWindow"}[backend]
    factory = getattr(vtk, name, None)
    if factory is None:
        raise RuntimeError(name + " is unavailable in this VTK build. Use ARX_RENDER_BACKEND=native, or the portable CPU path tracer.")
    window = factory()
    window.SetOffScreenRendering(1)
    return window
