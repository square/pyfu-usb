# Copyright 2022 Block, Inc.
"""Test functions for getting info from USB descriptors of DFU devices."""

from unittest import mock

import usb

from pyfu_usb.descriptor import (
    _DFU_DESCRIPTOR_ID,
    DfuDescriptor,
    DfuSeMemoryLayout,
    get_dfu_descriptor,
    get_memory_layout,
)


def test_get_dfu_descriptor_dfu_device(mock_usb_device: mock.Mock) -> None:
    """Test get_dfu_descriptor."""
    with mock.patch("usb.core.Interface", spec=True) as mock_iface:
        mock_usb_device.__iter__.return_value = [[mock_iface]]
        mock_iface.extra_descriptors = [
            9,
            _DFU_DESCRIPTOR_ID,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
        ]
        desc = get_dfu_descriptor(mock_usb_device)
        assert isinstance(desc, DfuDescriptor)
        assert desc.bmAttributes == 0
        assert desc.wDetachTimeOut == 0
        assert desc.wTransferSize == 0
        assert desc.bcdDFUVersion == 0


def test_get_dfu_descriptor_non_dfu_device(mock_usb_device: mock.Mock) -> None:
    """Test get_dfu_descriptor."""
    with mock.patch("usb.core.Interface", spec=True) as mock_iface:
        mock_usb_device.__iter__.return_value = [[mock_iface]]
        mock_iface.extra_descriptors = [0x00]
        assert get_dfu_descriptor(mock_usb_device) is None


def test_get_memory_layout(
    mock_usb_device: mock.Mock, mock_usb_get_string: mock.Mock
) -> None:
    """Test get_memory_layout."""
    # STM32F2 memory layout string
    mock_usb_get_string.return_value = "/0x08000000/04*016Kg,01*064Kg,07*128Kg"

    memory_layout = get_memory_layout(mock_usb_device, 0)
    assert isinstance(memory_layout, list)

    # Three segments are defined in the string
    assert len(memory_layout) == 3
    seg1 = memory_layout[0]
    seg2 = memory_layout[1]
    seg3 = memory_layout[2]

    def _check_seg_last_addr(seg: DfuSeMemoryLayout) -> None:
        assert seg.last_addr == seg.addr + seg.num_pages * seg.page_size - 1

    assert seg1.addr == 0x8000000
    assert seg1.num_pages == 4
    assert seg1.page_size == 1 << 14
    _check_seg_last_addr(seg1)

    assert seg2.addr == seg1.last_addr + 1
    assert seg2.num_pages == 1
    assert seg2.page_size == 1 << 16
    _check_seg_last_addr(seg2)

    assert seg3.addr == seg2.last_addr + 1
    assert seg3.num_pages == 7
    assert seg3.page_size == 1 << 17
    _check_seg_last_addr(seg2)


def test_get_memory_layout_no_string(
    mock_usb_device: mock.Mock, mock_usb_get_string: mock.Mock
) -> None:
    """Test get_memory_layout returns an empty list when no string is found."""
    mock_usb_get_string.side_effect = usb.core.USBError("No string for you.")

    memory_layout = get_memory_layout(mock_usb_device, 0)
    assert isinstance(memory_layout, list)
    assert len(memory_layout) == 0
