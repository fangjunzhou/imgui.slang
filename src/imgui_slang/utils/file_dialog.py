"""
Asynchronous file dialog module using portable_file_dialogs.
"""

import asyncio
from typing import List
from concurrent.futures import ProcessPoolExecutor
from imgui_bundle import portable_file_dialogs


def open_file_process(
    title: str,
    default_path: str,
    filters: List[str],
    options: portable_file_dialogs.opt,
) -> List[str]:
    """Runner function for file dialog in a separate process.

    :param title: The title of the file dialog window.
    :param default_path: The default path to open the dialog in.
    :param filters: List of file filters (e.g., ["Text Files", "*.txt"]).
    :param options: portable_file_dialogs options.
    :return:
    """
    of = portable_file_dialogs.open_file(
        title=title, default_path=default_path, filters=filters, options=options
    )
    return of.result()


def save_file_process(
    title: str,
    default_path: str,
    filters: List[str],
    options: portable_file_dialogs.opt,
) -> List[str]:
    """Runner function for save file dialog in a separate process.

    :param title: The title of the file dialog window.
    :param default_path: The default path to open the dialog in.
    :param filters: List of file filters (e.g., ["Text Files", "*.txt"]).
    :param options: portable_file_dialogs options.
    :return:
    """
    sf = portable_file_dialogs.save_file(
        title=title, default_path=default_path, filters=filters, options=options
    )
    return sf.result()


async def async_open_file_dialog(
    title: str,
    default_path: str,
    filters: List[str],
    options: portable_file_dialogs.opt,
) -> List[str]:
    """Asynchronously open a file dialog using multiprocessing.

    This function runs the blocking file dialog in a separate process to avoid
    blocking the main event loop.

    :param title: The title of the file dialog window.
    :param default_path: The default path to open the dialog in.
    :param filters: List of file filters (e.g., ["Text Files", "*.txt"]).
    :param options: portable_file_dialogs options.
    :return:
    """
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            open_file_process,
            title,
            default_path,
            filters,
            options,
        )
    return result


async def async_save_file_dialog(
    title: str,
    default_path: str,
    filters: List[str],
    options: portable_file_dialogs.opt,
) -> List[str]:
    """Asynchronously open a save file dialog using multiprocessing.

    This function runs the blocking file dialog in a separate process to avoid
    blocking the main event loop.

    :param title: The title of the file dialog window.
    :param default_path: The default path to open the dialog in.
    :param filters: List of file filters (e.g., ["Text Files", "*.txt"]).
    :param options: portable_file_dialogs options.
    :return:
    """
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            save_file_process,
            title,
            default_path,
            filters,
            options,
        )
    return result
