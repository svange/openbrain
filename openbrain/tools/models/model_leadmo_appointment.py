from pydantic import Field, BaseModel
from typing import Optional


class LeadmoAppointmentAdaptor(BaseModel):
    """The schema for the tool's input."""
    # startTime: str = Field(..., description="The start time of the appointment.")
    # endTime: str = Field(..., description="The end time of the appointment.")
    # title: str = Field(..., description="The title of the appointment.")
    # appointmentLocation: str = Field(..., description="The location of the appointment. This can be 'zoom', 'phone', 'in-person', etc.")
    #
    # phone: str = Field(..., description="The phone number of the contact for whom the appointment is being scheduled. Example: +1 888-888-8888")
    selectedSlot: str = Field(..., description="The time slot of the appointment. Example: 2021-02-05T11:00:00+05:30")
    selectedTimezone: str = Field(..., description="The timezone of the appointment. Example: Asia/Calcutta")
    title: str = Field(..., description="The title of the appointment. Example: Best Event")
    calendarNotes: str = Field(..., description="The notes for the appointment. Example: Worried about deductible.")

class LeadmoAppointment(BaseModel):
    """The schema for the tool's input."""
    email: str = Field(..., description="The email of the contact for whom the appointment is being scheduled. Example: me@mail.com")
    phone: str = Field(..., description="The phone number of the contact for whom the appointment is being scheduled. Example: +1 888-888-8888")
    selectedSlot: str = Field(..., description="The time slot of the appointment. Example: 2021-02-05T11:00:00+05:30")
    selectedTimezone: str = Field(..., description="The timezone of the appointment. Example: Asia/Calcutta")
    calendarId: str = Field(..., description="The ID of the calendar for the appointment.")
    firstName: str = Field(..., description="The first name of the contact for whom the appointment is being scheduled. Example: John")
    lastName: str = Field(..., description="The last name of the contact for whom the appointment is being scheduled. Example: Deo")
    name: str = Field(..., description="The full name of the contact for whom the appointment is being scheduled. Example: John Deo")
    title: str = Field(..., description="The title of the appointment. Example: Best Event")
    address1: str = Field(..., description="The address of the appointment. Example: Tonkawa Trail W")
    city: str = Field(..., description="The city of the appointment. Example: Austin")
    state: str = Field(..., description="The state of the appointment. Example: Texas")
    calendarNotes: str = Field(..., description="The notes for the appointment. Example: Worried about deductible.")

    startTime: str = Field(..., description="The start time of the appointment.")
    endTime: str = Field(..., description="The end time of the appointment.")
    title: str = Field(..., description="The title of the appointment.")
    appointmentStatus: Optional[str] = Field(default="new", description="The status of the appointment.")
    address: str = Field(..., description="The address of the appointment.")
    ignoreDateRange: bool = Field(default=False, description="Whether to ignore the date range.")
    toNotify: bool = Field(default=False, description="Whether to notify the user of the appointment.")
    assignedUserId: str = Field(..., description="The ID of the contact for whom the appointment is being scheduled.")
    locationId: str = Field(..., description="The ID of the location where the appointment is to be held.")
