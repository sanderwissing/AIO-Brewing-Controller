# simple_pid.py - Simple PID controller implementation

import time

class PID:
    """
    Simple PID controller implementation for brewing temperature control
    """
    
    def __init__(self, kp=1.0, ki=0.0, kd=0.0, setpoint=0.0, 
                 output_limits=(None, None), auto_mode=True):
        """
        Initialize PID controller
        
        :param kp: Proportional gain
        :param ki: Integral gain  
        :param kd: Derivative gain
        :param setpoint: Target setpoint
        :param output_limits: Tuple of (min, max) output limits
        :param auto_mode: Whether PID is active
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        
        self._auto_mode = auto_mode
        self._output_limits = output_limits
        
        # Internal state
        self._last_input = None
        self._last_time = None
        self._integral = 0.0
        self._last_output = 0.0
        
        # Reset the PID
        self.reset()
    
    def __call__(self, input_val, dt=None):
        """
        Calculate PID output
        
        :param input_val: Current process variable (temperature)
        :param dt: Time delta in seconds (optional, will calculate if None)
        :return: PID output
        """
        if not self._auto_mode:
            return self._last_output
        
        now = time.ticks_ms()
        
        # Calculate dt if not provided
        if dt is None:
            if self._last_time is None:
                dt = 0.1  # Default dt for first call
            else:
                dt = time.ticks_diff(now, self._last_time) / 1000.0
        
        # Avoid division by zero
        if dt <= 0.0:
            dt = 0.1
            
        self._last_time = now
        
        # Calculate error
        error = self.setpoint - input_val
        
        # Proportional term
        proportional = self.kp * error
        
        # Integral term
        self._integral += error * dt
        integral = self.ki * self._integral
        
        # Derivative term  
        derivative = 0.0
        if self._last_input is not None:
            derivative = self.kd * (input_val - self._last_input) / dt
        
        # Calculate output
        output = proportional + integral - derivative  # Note: derivative is subtracted
        
        # Apply output limits
        if self._output_limits[0] is not None and output < self._output_limits[0]:
            output = self._output_limits[0]
        elif self._output_limits[1] is not None and output > self._output_limits[1]:
            output = self._output_limits[1]
            
        # Anti-windup: reset integral if output is saturated
        if (self._output_limits[0] is not None and output <= self._output_limits[0]) or \
           (self._output_limits[1] is not None and output >= self._output_limits[1]):
            self._integral -= error * dt  # Remove the contribution that caused saturation
        
        # Store values for next iteration
        self._last_input = input_val
        self._last_output = output
        
        return output
    
    def reset(self):
        """Reset PID internal state"""
        self._last_input = None
        self._last_time = None
        self._integral = 0.0
        self._last_output = 0.0
    
    @property
    def auto_mode(self):
        """Get auto mode status"""
        return self._auto_mode
    
    @auto_mode.setter  
    def auto_mode(self, enabled):
        """Set auto mode"""
        if enabled and not self._auto_mode:
            # Switching from manual to auto
            self.reset()
        self._auto_mode = enabled
    
    @property
    def output_limits(self):
        """Get output limits"""
        return self._output_limits
    
    @output_limits.setter
    def output_limits(self, limits):
        """Set output limits as (min, max) tuple"""
        if limits is None:
            self._output_limits = (None, None)
        else:
            self._output_limits = (limits[0], limits[1])
    
    @property 
    def tunings(self):
        """Get PID tunings"""
        return (self.kp, self.ki, self.kd)
    
    @tunings.setter
    def tunings(self, tunings):
        """Set PID tunings"""
        self.kp, self.ki, self.kd = tunings