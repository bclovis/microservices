import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      [type]="type"
      [disabled]="disabled"
      (click)="onClick.emit($event)"
      [ngClass]="{
        'w-full': fullWidth,
        'opacity-50 cursor-not-allowed': disabled,
        'bg-poke-red hover:bg-red-600 text-white': variant === 'primary',
        'bg-poke-blue hover:bg-blue-600 text-white': variant === 'secondary',
        'bg-red-600 hover:bg-red-700 text-white': variant === 'danger',
        'bg-transparent hover:bg-white/10 text-white': variant === 'ghost',
        'px-6 py-3 rounded-xl font-semibold transition-all duration-200 shadow-md active:scale-95': true
      }"
    >
      <ng-content></ng-content>
    </button>
  `,
  styles: []
})
export class ButtonComponent {
  @Input() type: 'button' | 'submit' | 'reset' = 'button';
  @Input() variant: 'primary' | 'secondary' | 'danger' | 'ghost' = 'primary';
  @Input() fullWidth: boolean = false;
  @Input() disabled: boolean = false;
  @Output() onClick = new EventEmitter<Event>();
}
