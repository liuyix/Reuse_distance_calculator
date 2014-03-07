function D = filter_db(X, gate, fname)

fid = fopen(fname, 'w');
D = zeros(length(X), 1);
x_max = max(max(abs(X)));
if gate > 0
    alpha = gate;
else
    alpha = 0.5;
end;

fprintf(fid, 'length\t%d\ngate\t%.1f\nx_max\t%d\n\n', length(X), alpha, x_max);
% beta = 0.1;
% last_idx = 0;
for i = 1:length(X)
    x = X(i,1);
    if abs(x) > x_max * alpha
        D(i, 1) = abs(x);
        fprintf(fid, '%d\t%d\n', abs(x), i);
%         idx = i;
%         if (idx - last_idx) > beta * length(X)
%             D(i, 1) = x;
%             last_idx = idx;
%            disp(x);
%            disp(i);
%         end
    end
end
plot(D);

        
        