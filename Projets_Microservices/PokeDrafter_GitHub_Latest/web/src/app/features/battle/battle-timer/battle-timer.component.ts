import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-battle-timer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative w-16 h-16 flex items-center justify-center">
      <svg class="w-full h-full transform -rotate-90" viewBox="0 0 64 64">
        <circle
          cx="32"
          cy="32"
          r="28"
          stroke="currentColor"
          stroke-width="4"
          fill="transparent"
          class="text-gray-100"
        />
        <circle
          cx="32"
          cy="32"
          r="28"
          stroke="currentColor"
          stroke-width="4"
          fill="transparent"
          [attr.stroke-dasharray]="circumference"
          [attr.stroke-dashoffset]="dashoffset"
          [class.text-green-500]="timeLeft > 30"
          [class.text-yellow-500]="timeLeft <= 30 && timeLeft > 10"
          [class.text-red-500]="timeLeft <= 10"
          stroke-linecap="round"
          class="transition-all duration-1000 ease-linear"
        />
      </svg>
      <span class="absolute text-xs font-black tracking-tighter" [class.text-red-600]="timeLeft <= 10" [class.animate-pulse]="timeLeft <= 10">
        {{ timeLeft }}s
      </span>
    </div>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class BattleTimerComponent implements OnInit, OnDestroy {
  @Input() duration: number = 90;
  @Output() timeout = new EventEmitter<void>();

  timeLeft: number = 90;
  circumference = 2 * Math.PI * 28;
  private timer: any;

  ngOnInit() {
    this.timeLeft = this.duration;
    this.startTimer();
  }

  ngOnDestroy() {
    this.stopTimer();
  }

  startTimer() {
    this.stopTimer();
    this.timer = setInterval(() => {
      if (this.timeLeft > 0) {
        this.timeLeft--;
      }
      
      if (this.timeLeft <= 0) {
        this.stopTimer();
        this.timeout.emit();
      }
    }, 1000);
  }

  stopTimer() {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }

  reset() {
    this.timeLeft = this.duration;
    this.startTimer();
  }

  get dashoffset() {
    const progress = this.timeLeft / this.duration;
    return this.circumference * (1 - progress);
  }
}
