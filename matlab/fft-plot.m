function fft_wrapper(data_vec, name)

result = abs(fftshift(data_vec));
saveas(plot(result), name)

end;
